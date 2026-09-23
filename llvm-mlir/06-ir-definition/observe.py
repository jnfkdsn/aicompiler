#!/usr/bin/env python3
"""Build the lesson dialect and show the evidence behind each IR-definition chapter."""
import argparse
from datetime import datetime
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--section', choices=['all', 'interfaces', 'types', 'regions', 'assembly'], default='all')
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    workspace = project.parents[2]
    build = workspace / 'artifacts/builds/mlir-ir-definition'
    llvm = workspace / 'artifacts/builds/mlir-20.1.8'
    out = workspace / 'artifacts/logs/mlir-ir-definition' / datetime.now().strftime('%Y-%m-%d-%H%M%S-%f')
    out.mkdir(parents=True)

    def run(name, command, show=True):
        result = subprocess.run([str(x) for x in command], capture_output=True, text=True, timeout=240)
        (out / (name + '.stdout.txt')).write_text(result.stdout)
        (out / (name + '.stderr.txt')).write_text(result.stderr)
        if show or result.returncode:
            print(result.stdout, end='')
            print(result.stderr, end='')
        if result.returncode:
            raise SystemExit(f'{name} failed; see {out}')
        return result

    def heading(title):
        print('\n' + title, flush=True)

    def show_input(name):
        heading(f'输入：{name}.mlir')
        print((project / (name + '.mlir')).read_text(), end='')

    heading('使用现有 LLVM/MLIR 库构建本章工具')
    run('configure', ['cmake', '-S', project, '-B', build, '-G', 'Ninja',
        f'-DMLIR_DIR={llvm}/lib/cmake/mlir', f'-DLLVM_DIR={llvm}/lib/cmake/llvm',
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_COMPILER=/usr/bin/clang++',
        '-DCMAKE_C_COMPILER=/usr/bin/clang'], show=False)
    run('build', ['cmake', '--build', build, '-j2'], show=False)
    opt = build / 'lesson-opt'
    report = '--pass-pipeline=builtin.module(func.func(lesson-report))'
    if args.section in ('all', 'interfaces'):
        show_input('interfaces')
        heading('1. 已注册外部范围模型：查询效果、使用情况与范围')
        run('interfaces-model', [opt, project / 'interfaces.mlir', report, '-o', '/dev/null'])
        show_input('direct')
        heading('先走通直接实现：无需外部模型，操作自己提供范围答案')
        run('direct-scalar', [build / 'lesson-opt-no-model', project / 'direct.mlir', report])
        heading('2. 同一 IR，不注册范围模型：观察哪条信息消失')
        run('interfaces-no-model', [build / 'lesson-opt-no-model', project / 'interfaces.mlir', report, '-o', '/dev/null'])
        heading('3. canonicalize 后：有无效果信息怎样影响死代码删除')
        run('interfaces-cleanup', [opt, project / 'interfaces.mlir', '--canonicalize', '--verify-each'])
    if args.section in ('all', 'types'):
        show_input('types')
        heading('4. 操作直接实现范围接口；ODS 已知类型/属性种类，可省略打印前缀')
        run('types-report', [opt, project / 'types.mlir', report])
        heading('5. 同一对象的通用格式：观察属性与结果类型的位置')
        run('types-generic', [opt, project / 'types.mlir', '--mlir-print-op-generic'])
        heading('6. 类型身份与 checked 构造：最后一项故意请求非法范围并处理诊断')
        run('type-probe', [build / 'type-probe'])
    if args.section in ('all', 'regions'):
        show_input('scope')
        heading('7. 解析并验证：沿输入/Block 参数/yield/结果逐项对应')
        run('scope', [opt, project / 'scope.mlir'])
        heading('8. 通用格式：包括 yield 在内的所有操作都显示完整字段')
        run('scope-generic', [opt, project / 'scope.mlir', '--mlir-print-op-generic'])
    if args.section in ('all', 'assembly'):
        show_input('assembly')
        heading('9. 手写 printer 输出')
        normal = run('assembly', [opt, project / 'assembly.mlir'])
        heading('10. 通用打印再解析：关键字恢复，参数引用与额外属性保留')
        generic = run('assembly-generic', [opt, project / 'assembly.mlir', '--mlir-print-op-generic'])
        path = out / 'assembly-generic.mlir'
        path.write_text(generic.stdout)
        roundtrip = run('assembly-roundtrip', [opt, path])
        if normal.stdout != roundtrip.stdout:
            raise SystemExit('Assembly roundtrip changed normalized IR')
    print(f'\n生成代码：{build}/*.inc')
    print(f'本次输入对应的输出与诊断：{out}')


if __name__ == '__main__':
    main()
