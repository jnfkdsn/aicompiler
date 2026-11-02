#!/usr/bin/env python3
"""Show inputs, queried facts, IR changes, and optional CPU results."""
import argparse
from experiment import Experiment, INSPECT, OPT, PROJECT, OPTIMIZE, log_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topic', choices=['dominance','alias','cache','constants','legality'], default='dominance')
    parser.add_argument('--native', action='store_true', help='run 15 C observations before and after optimization')
    args = parser.parse_args()
    e = Experiment(log_directory(), show=True)
    if not INSPECT.exists(): e.build()
    fixture = {'dominance':'dominance', 'alias':'alias', 'cache':'dominance',
               'constants':'constants', 'legality':'optimizations'}[args.topic]
    path = PROJECT/(fixture+'.mlir')
    print('输入 IR：\n'+path.read_text(), flush=True)
    if args.topic == 'legality':
        print('预期：重复加法和死乘法消失；load/store/load 保留；循环加法外提、除法保留。', flush=True)
        e.run('optimized', [OPT,path,*OPTIMIZE,'--verify-each'])
    elif args.topic == 'cache':
        print('正确模式：9 被复用一次，插入常量后重算成 10。', flush=True)
        e.query('cache',path)
        print('错误模式：声明保留已失效分析，IR 合法但 cached=9、fresh=10。', flush=True)
        e.query('stale',path)
    else:
        e.query(args.topic,path)
        if args.topic == 'dominance':
            print('CFG 合流输入：\n'+(PROJECT/'cfg.mlir').read_text(),flush=True)
            e.query('cfg',PROJECT/'cfg.mlir')
        if args.topic == 'constants':
            e.run('constant-transform',[OPT,path,'--sccp','--canonicalize'])
            print('范围输入：\n'+(PROJECT/'ranges.mlir').read_text(),flush=True)
            e.query('ranges',PROJECT/'ranges.mlir')
    if args.native: e.native()
    print('完整命令与输出：'+str(e.output))
    if any(not item['passed'] for item in e.checks): raise SystemExit(1)


if __name__=='__main__': main()
