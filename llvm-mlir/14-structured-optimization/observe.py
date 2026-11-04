#!/usr/bin/env python3
"""Print real tiling/fusion/interchange stages and dependence evidence."""
import argparse
from experiment import Experiment,INSPECT,PROJECT,log_directory

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['base','affine-tile','fused','tiled','swapped','dependence'],default='affine-tile')
    p.add_argument('--native',action='store_true');a=p.parse_args()
    e=Experiment(log_directory(),show=True)
    if a.stage=='dependence':
        if not INSPECT.exists():e.build()
        for name in ['affine-add','wave']:
            print('输入：\n'+(PROJECT/(name+'.mlir')).read_text(),flush=True)
            e.run(name+'-dependence',[INSPECT,PROJECT/(name+'.mlir')])
    else:
        name='affine-add' if a.stage=='affine-tile' else 'elementwise'
        print('输入：\n'+(PROJECT/(name+'.mlir')).read_text(),flush=True)
        e.stage(a.stage)
    if a.native:e.native()
    print('case 行依次为名称、核对元素数、错误数；sample 行提供具体坐标结果。')
    print('日志：'+str(e.output))
    if any(not c['passed'] for c in e.checks):raise SystemExit(1)

if __name__=='__main__':main()
