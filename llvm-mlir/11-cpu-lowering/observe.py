#!/usr/bin/env python3
import argparse
from experiment import Commands, PROJECT, LLVM, log_directory


def main():
    parser = argparse.ArgumentParser(description='Observe lowering, translation, C ABI execution, or JIT.')
    parser.add_argument('--example', choices=sorted(p.stem for p in PROJECT.glob('*.mlir')), default='add-into')
    parser.add_argument('--stage', choices=['input', 'loops', 'cf', 'llvm', 'llvmir', 'asm'], default='loops')
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--jit', action='store_true')
    args = parser.parse_args()
    out = log_directory(); c = Commands(out, show=True)
    print('输入：\n' + (PROJECT / (args.example + '.mlir')).read_text())
    stage = 'llvm' if args.stage in ('llvmir', 'asm') else args.stage
    lowered = c.stage(args.example, stage)
    if args.stage in ('llvmir', 'asm'):
        ir = c.artifact(args.example + '-translation', [LLVM / 'bin/mlir-translate', lowered, '--mlir-to-llvmir'], '.ll')
        if args.stage == 'asm':
            c.artifact(args.example + '-assembly', [LLVM / 'bin/llc', ir, '-O0', '-o', '-'], '.s')
    if args.native:
        c.show = False
        for item in c.native():
            print(f"{item['name']}: actual={item['actual']:g}, expected={item['expected']:g}")
    if args.jit:
        c.show = True
        ir = c.stage('jit', 'llvm')
        result = c.run('jit-execute', [LLVM / 'bin/mlir-runner', ir, '-e', 'main', '-entry-point-result=i32'])
        c.check('jit-value', result.stdout.strip() == '42')
    print('日志：' + str(out))
    if any(not item['passed'] for item in c.checks): raise SystemExit('An observation failed; inspect logs.')


if __name__ == '__main__':
    main()
