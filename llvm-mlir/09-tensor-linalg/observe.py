#!/usr/bin/env python3
"""Print tensor input and concrete buffer/loop IR; optionally execute numeric cases."""
import argparse
from experiment import Commands, PROJECT, OPT, BUFFER_FLAGS, LOOP_FLAGS, log_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--example', default='add', choices=sorted(p.stem for p in PROJECT.glob('*.mlir')))
    parser.add_argument('--numeric', action='store_true', help='Also compile and run all small numeric examples')
    args = parser.parse_args()
    out = log_directory('tensor-linalg-observe')
    commands = Commands(out, show=True)
    source = PROJECT / (args.example + '.mlir')
    print('输入：先预测值、shape 和访问关系。\n' + source.read_text())
    print('Buffer 阶段：观察结果存储、旧值和复制。')
    commands.artifact('buffer', [OPT, source, *BUFFER_FLAGS, '--verify-each'])
    print('Loop 阶段：对照每个迭代点的 load、标量计算和 store。')
    commands.artifact('loops', [OPT, source, *LOOP_FLAGS, '--verify-each'])
    if args.numeric:
        # Keep long generated IR in logs; present values grouped by source function.
        commands.show = False
        observations = commands.numeric()
        group = None
        for item in observations:
            if item['function'] != group:
                group = item['function']
                print('\n@' + group)
            print(f"  {item['position']}: actual={item['actual']}, expected={item['expected']}")
    print('\n命令、完整输出与数值记录：' + str(out))
    if any(not c['passed'] for c in commands.checks):
        raise SystemExit('Some checks failed; inspect the log directory.')


if __name__ == '__main__':
    main()
