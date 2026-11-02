#!/usr/bin/env python3
"""Show scalar lowering, Softmax IR stages or native error summaries."""
import argparse
from experiment import Experiment,OPT,PROJECT,log_directory

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--example',choices=['math','index','softmax','row-softmax'],default='softmax')
    p.add_argument('--stage',choices=['input','buffer','llvm'],default='buffer')
    p.add_argument('--native',action='store_true',help='compare both CPU implementations with a double oracle')
    args=p.parse_args();e=Experiment(log_directory(),show=True)
    print('原始输入：\n'+(PROJECT/(args.example+'.mlir')).read_text(),flush=True)
    if args.example=='softmax' and args.stage=='buffer':
        print('观察 Max[M]、E[M,N]、Sum[M]、Y[M,N] 四个分配及其先后读写。',flush=True)
    e.stage(args.example,args.stage)
    if args.native:e.native()
    print('日志：'+str(e.output))
    if any(not c['passed'] for c in e.checks):raise SystemExit(1)

if __name__=='__main__':main()
