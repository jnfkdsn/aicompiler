#!/usr/bin/env python3
"""Observe type conversion at producer, function and region boundaries."""
import argparse
from datetime import datetime
from pathlib import Path
import shlex
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-only', action='store_true')
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    workspace = project.parents[2]
    build = workspace / 'artifacts/builds/mlir-type-conversion'
    llvm = workspace / 'artifacts/builds/mlir-20.1.8'
    out = workspace / 'artifacts/logs/mlir-type-conversion' / datetime.now().strftime('%Y-%m-%d-%H%M%S-%f')
    out.mkdir(parents=True)

    def run(name, command, expected=0, show=True):
        command = [str(x) for x in command]
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        (out / (name + '.command.txt')).write_text(shlex.join(command) + '\n')
        (out / (name + '.stdout.txt')).write_text(result.stdout)
        (out / (name + '.stderr.txt')).write_text(result.stderr)
        if show or result.returncode != expected:
            print('$ ' + shlex.join(command), flush=True)
            print(result.stdout, end='')
            print(result.stderr, end='')
            print(f'exit={result.returncode} (expected {expected})', flush=True)
        if result.returncode != expected:
            raise SystemExit(f'{name} failed; see {out}')
        return result

    run('configure', ['cmake', '-S', project, '-B', build, '-G', 'Ninja',
        f'-DMLIR_DIR={llvm}/lib/cmake/mlir', f'-DLLVM_DIR={llvm}/lib/cmake/llvm',
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
        '-DCMAKE_C_COMPILER=/usr/bin/clang'], show=False)
    run('build', ['cmake', '--build', build, '-j2'], show=False)
    if args.build_only:
        print(f'Built tools: {build}')
        return
    probe, opt = build / 'range-probe', build / 'range-opt'
    cases = [
        ('生产者、return 与函数签名一起变成 i32', 'full', 'limit', 0),
        ('相同完整路径不需要遗留桥接', 'full-no-bridge', 'limit', 0),
        ('保留旧返回接口，观察 i32 到 range 的边界', 'partial', 'limit', 0),
        ('移除桥接回调，观察仍存活的旧使用者', 'partial-no-bridge', 'limit', 1),
        ('函数、调用点与 return 同步改变', 'full', 'calls', 0),
        ('只漏掉 call 规则', 'no-call', 'calls', 1),
        ('scope 入口、Block 参数、yield 与结果一致转换', 'full', 'scope', 0),
        ('只漏掉 yield 规则', 'no-yield', 'scope', 1),
        ('分支实参与目标 Block 参数', 'full', 'branch', 0),
        ('可转换性分析报告 limit 可转换，并保留原输入', 'analysis', 'analysis-mixed', 0),
        ('相同混合输入不满足 full 目标', 'full', 'analysis-mixed', 1),
        ('递归合法性使整个函数内部被跳过', 'recursive', 'limit', 0),
    ]
    partial = None
    for title, mode, name, expected in cases:
        print('\n' + title)
        print((project / (name + '.mlir')).read_text())
        result = run(mode + '-' + name, [probe, mode, project / (name + '.mlir')], expected)
        if mode == 'partial':
            partial = out / 'partial.mlir'
            partial.write_text(result.stdout)
    print('\n清理不能删除仍被旧 return 使用的单向占位 cast。')
    run('reconcile-live', [opt, partial, '--reconcile-unrealized-casts'])
    print('\n继续转换函数与 return 后，检查不再有未落实的 cast。')
    run('finish', [probe, 'finish', partial])
    print('\n互为往返的 cast 可以消解：')
    print((project / 'cast-roundtrip.mlir').read_text())
    run('reconcile-roundtrip', [opt, project / 'cast-roundtrip.mlir', '--reconcile-unrealized-casts'])
    print(f'\n命令、输出和诊断：{out}')


if __name__ == '__main__':
    main()
