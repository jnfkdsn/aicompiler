#!/usr/bin/env python3
"""Print the actual input, decisions, transformed IR, and optional numbers."""
import argparse
from experiment import (PROJECT, OPT, BUFFER_EXAMPLES, OWNERSHIP_EXAMPLES,
                        Commands, log_directory, stage_flags)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--example', choices=sorted(p.stem for p in PROJECT.glob('*.mlir')), default='preserve')
    parser.add_argument('--stage', choices=['input', 'analysis', 'buffer', 'ownership', 'dealloc'])
    parser.add_argument('--numeric', action='store_true')
    args = parser.parse_args()
    out = log_directory()
    c = Commands(out, show=True)
    print('输入：\n' + (PROJECT / (args.example + '.mlir')).read_text())
    stages = ([args.stage] if args.stage else ['analysis', 'buffer', 'dealloc']
              if args.example in BUFFER_EXAMPLES else ['ownership', 'dealloc']
              if args.example in OWNERSHIP_EXAMPLES else ['input'])
    for stage in stages:
        try:
            flags = stage_flags(args.example, stage)
        except ValueError as error:
            parser.error(str(error))
        print('\n阶段：' + stage, flush=True)
        c.artifact(stage + '-' + args.example, [OPT, PROJECT / (args.example + '.mlir'), *flags, '--verify-each'])
    if args.numeric:
        # Retain commands and raw outputs in the log, while keeping numeric
        # observations readable instead of printing two full LLVM modules.
        c.show = False
        for item in c.numeric():
            print(f"{item['suite']}/{item['name']}: actual={item['actual']}, expected={item['expected']}")
    print('日志：' + str(out))
    if any(not item['passed'] for item in c.checks):
        raise SystemExit('Observation did not match the expected result; inspect the log.')


if __name__ == '__main__':
    main()
