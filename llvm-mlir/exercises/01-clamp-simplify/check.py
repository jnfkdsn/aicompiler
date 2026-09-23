#!/usr/bin/env python3
"""Build the learner starter, show before/after IR, optionally check the target behavior."""
import argparse
from datetime import datetime
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['starter', 'solution'], default='starter')
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    workspace = project.parents[3]
    llvm = workspace / 'artifacts/builds/mlir-20.1.8'
    build = workspace / 'artifacts/builds/mlir-exercise-clamp'
    out = workspace / 'artifacts/logs/mlir-exercise-clamp' / datetime.now().strftime('%Y-%m-%d-%H%M%S-%f')
    out.mkdir(parents=True)

    def run(name, command, expected=0, show=False):
        result = subprocess.run([str(x) for x in command], capture_output=True, text=True, timeout=240)
        (out / (name + '.stdout.txt')).write_text(result.stdout)
        (out / (name + '.stderr.txt')).write_text(result.stderr)
        if show or result.returncode != expected:
            print(result.stdout, end='')
            print(result.stderr, end='')
        if result.returncode != expected:
            raise SystemExit(f'{name}: expected exit {expected}, got {result.returncode}. Logs: {out}')
        return result

    print('构建练习工具……', flush=True)
    run('configure', ['cmake', '-S', project, '-B', build, '-G', 'Ninja',
        f'-DMLIR_DIR={llvm}/lib/cmake/mlir', f'-DLLVM_DIR={llvm}/lib/cmake/llvm',
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
        '-DCMAKE_C_COMPILER=/usr/bin/clang'])
    run('build', ['cmake', '--build', build, '-j2'])
    opt = build / 'student-opt'
    pipeline = '--pass-pipeline=builtin.module(func.func(student-simplify-clamp))'
    print('\n输入 IR：', flush=True)
    run('before', [opt, project / 'input.mlir'], show=True)
    print('\n你的 Pass 输出：', flush=True)
    result = run('after', [opt, project / 'input.mlir', pipeline, '--verify-each'], show=True)
    after = out / 'after.mlir'
    after.write_text(result.stdout)
    run('diagnostics', [opt, project / 'invalid.mlir', '--verify-diagnostics', '-o', '/dev/null'])
    if args.stage == 'solution':
        run('goal', [llvm / 'bin/FileCheck', project / 'input.mlir', f'--input-file={after}'])
        again = run('second-run', [opt, after, pipeline, '--verify-each'])
        if again.stdout != result.stdout:
            raise SystemExit(f'Second application changed the output; see {out}')
        print('\n目标行为与重复应用检查通过；请再补充一个自己的边界用例和解释。')
    else:
        print('\n骨架构建、解析、Pass 运行与非法输入诊断检查通过。')
        print('starter 不检查优化是否完成。初始 TODO 会保留全部 clamp；完成后用 --stage solution。')
    print(f'记录：{out}')


if __name__ == '__main__':
    main()
