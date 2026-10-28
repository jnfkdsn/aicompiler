#!/usr/bin/env python3
"""Show clamp conversion, legality failures and partial/full contrasts."""
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
    build = workspace / 'artifacts/builds/mlir-dialect-conversion'
    llvm = workspace / 'artifacts/builds/mlir-20.1.8'
    out = workspace / 'artifacts/logs/mlir-dialect-conversion' / datetime.now().strftime('%Y-%m-%d-%H%M%S-%f')
    out.mkdir(parents=True)

    def run(name, command, expected=0, show=True):
        command = [str(x) for x in command]
        result = subprocess.run(command, capture_output=True, text=True, timeout=240)
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
    print('输入：一个合法的 clamp，目标阶段要求它消失。')
    print((project / 'input.mlir').read_text())
    run('pass', [build / 'my-convert-opt', project / 'input.mlir',
        '--pass-pipeline=builtin.module(my-clamp-to-arith)', '--verify-each'])
    cases = [
        ('缺少规则：目标要求仍未完成', 'full-no-rule', 'input', 1),
        ('缺少常量许可：展开路径不能合法化', 'partial-no-constant', 'input', 1),
        ('输入中还存在 addi；partial 允许原有未知操作', 'partial', 'mixed', 0),
        ('相同输入改用 full，addi 没有被目标接受', 'full', 'mixed', 1),
        ('i64 maxsi 符合自身定义，但不满足当前动态目标', 'partial-dynamic', 'wide', 1),
        ('两条 clamp 相连：观察第二条输入及两处 use', 'full', 'chain', 0),
    ]
    for i, (title, mode, fixture, expected) in enumerate(cases):
        print('\n' + title, flush=True)
        print((project / (fixture + '.mlir')).read_text())
        run(f'case-{i}', [build / 'conversion-probe', mode, project / (fixture + '.mlir')], expected)
    print(f'\n输入、命令、输出和诊断：{out}')


if __name__ == '__main__':
    main()
