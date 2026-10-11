#!/usr/bin/env python3
"""Show stage 01 build inputs, generated accessors and the same IR in two formats."""
import argparse
from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-task', action='store_true', help='Copy stage 01 to work/01-rename once; never overwrite')
    parser.add_argument('--task', action='store_true', help='Build the learner work copy instead of the reference stage')
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    workspace = project.parents[2]
    reference = project / 'stages/01-minimal'
    work = project / 'work/01-rename'
    if args.prepare_task:
        if work.exists():
            print(f'保留已有练习目录，不覆盖：{work}')
        else:
            shutil.copytree(reference, work)
            print(f'练习副本已创建：{work}')
        return
    source = work if args.task else reference
    if not source.is_dir():
        raise SystemExit('请先运行 observe.py --prepare-task')
    build = workspace / 'artifacts/builds' / ('my-dialect-01-task' if args.task else 'my-dialect-01')
    llvm = workspace / 'artifacts/builds/mlir-20.1.8'
    out = workspace / 'artifacts/logs/my-dialect-01' / datetime.now().strftime('%Y-%m-%d-%H%M%S-%f')
    out.mkdir(parents=True)

    def run(name, command, show=False):
        result = subprocess.run([str(x) for x in command], capture_output=True, text=True, timeout=240)
        (out / (name + '.stdout.txt')).write_text(result.stdout)
        (out / (name + '.stderr.txt')).write_text(result.stderr)
        if show or result.returncode:
            print(result.stdout, end='', flush=True)
            print(result.stderr, end='', flush=True)
        if result.returncode:
            raise SystemExit(f'{name} failed: {out}')
        return result.stdout

    print('1. 本次构建的 ODS 定义：', flush=True)
    print((source / 'MyOps.td').read_text(), flush=True)
    print('2. TableGen 生成 C++，随后编译并链接 my-opt（完整构建日志保存在 artifacts）', flush=True)
    run('configure', ['cmake', '-S', source, '-B', build, '-G', 'Ninja',
        f'-DMLIR_DIR={llvm}/lib/cmake/mlir', f'-DLLVM_DIR={llvm}/lib/cmake/llvm',
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
        '-DCMAKE_C_COMPILER=/usr/bin/clang'])
    run('build', ['cmake', '--build', build, '-j2'])
    print(f'\n3. 生成文件：{build}/MyOps.h.inc（以下是实际行号与摘录）', flush=True)
    for n, line in enumerate((build / 'MyOps.h.inc').read_text().splitlines(), 1):
        if re.search(r'class AddOp :|get(Lhs|Rhs|Left|Result)\(', line):
            print(f'{n}: {line.strip()}')
    print('\n4. 输入文件：', flush=True)
    print((source / 'input.mlir').read_text(), flush=True)
    opt = build / 'my-opt'
    print('5. 解析、验证并正常打印：', flush=True)
    normal = run('custom', [opt, source / 'input.mlir'], show=True)
    print('6. 同一对象的通用打印：', flush=True)
    generic = run('generic', [opt, source / 'input.mlir', '--mlir-print-op-generic'], show=True)
    path = out / 'generic.mlir'
    path.write_text(generic)
    reparsed = run('roundtrip', [opt, path])
    if reparsed != normal:
        raise SystemExit('通用打印往返改变了规范化 IR，请检查 parser/printer。')
    print(f'7. 通用格式再解析后的正常输出相同。\n生成文件：{build}\n本次日志：{out}')
    print('本阶段构造和验证 IR，没有执行加法，也没有运行 lowering。')


if __name__ == '__main__':
    main()
