#!/usr/bin/env python3
"""Print commands and representations, not only a passed count."""
import argparse
from experiment import Experiment, log_directory

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stage', choices=['mapping', 'outline', 'lower', 'models', 'device', 'all'], default='outline')
args = parser.parse_args()
out = log_directory()
e = Experiment(out, show=True)
for stage, action in [('mapping', e.mapping), ('outline', e.outlining),
                      ('lower', e.lowering), ('models', e.models), ('device', e.serialize)]:
    if args.stage in [stage, 'all']:
        print('\n观察阶段：' + stage)
        action()
print('\n完整命令和产物：' + str(out))
