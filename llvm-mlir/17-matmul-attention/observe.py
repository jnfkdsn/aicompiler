#!/usr/bin/env python3
import argparse
from experiment import Experiment,OPT,PROJECT,log_directory
parser=argparse.ArgumentParser(description='Print Matmul schedules, Attention IR or native observations.')
parser.add_argument('--stage',choices=['tile','unroll','attention','online','native'],default='tile')
args=parser.parse_args();out=log_directory();e=Experiment(out,show=True)
if args.stage in ['tile','unroll']:e.scheduled(args.stage)
elif args.stage=='native':e.native()
else:e.artifact(args.stage,[OPT,PROJECT/(args.stage+'.mlir')])
print('保存的命令与产物：'+str(out))
