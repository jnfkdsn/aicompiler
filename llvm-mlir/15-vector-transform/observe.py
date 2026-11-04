#!/usr/bin/env python3
"""Observe actual vector IR, lowering, diagnostics and native results."""
import argparse
from experiment import Experiment,OPT,PROJECT,log_directory,schedule

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['automatic','values','reduction','transfer','masked','split','suppress'],default='automatic')
    p.add_argument('--llvm',action='store_true');p.add_argument('--native',action='store_true')
    p.add_argument('--benchmark',action='store_true');a=p.parse_args()
    e=Experiment(log_directory(),show=True)
    source=PROJECT/(('elementwise' if a.stage in ['automatic','suppress'] else a.stage)+'.mlir')
    print('输入：\n'+source.read_text(),flush=True)
    if a.stage=='automatic':result=e.automatic()
    elif a.stage=='suppress':result=e.artifact('suppressed',[OPT,source,*schedule('suppress')])
    else:result=e.artifact(a.stage,[OPT,source])
    if a.llvm:e.lower(a.stage,result,patterns=a.stage in ['values','reduction'])
    if a.native or a.benchmark:e.native(benchmark=a.benchmark)
    print('case：名称 / 检查元素数 / 错误数；sample：具体结果；bench：方案 / N / 重复次数 / min / median / max（ns/调用）。')
    print('日志：'+str(e.output))
    if any(not c['passed'] for c in e.checks):raise SystemExit(1)

if __name__=='__main__':main()
