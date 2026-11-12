"""Capture pass failure, replay it, reduce it and test the causal predicate."""
from datetime import datetime
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
BUILD=WORKSPACE/'artifacts/builds/mlir-debug-testing'
def log_directory():
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')+'-debug-testing')
    out.mkdir(parents=True);return out
class Experiment:
    def __init__(self,out,show=False):self.out,self.show,self.checks=out,show,[]
    def check(self,name,ok):self.checks.append({'name':name,'passed':bool(ok)})
    def run(self,name,cmd,expected=0):
        cmd=list(map(str,cmd));r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
        for suffix,text in [('command.txt',shlex.join(cmd)+'\n'),('stdout.txt',r.stdout),('stderr.txt',r.stderr)]:
            (self.out/(name+'.'+suffix)).write_text(text)
        self.check(name,r.returncode==expected)
        if self.show or r.returncode!=expected:print('$ '+shlex.join(cmd)+'\n'+r.stdout+r.stderr)
        return r
    def build(self):
        self.run('configure',['cmake','-G','Ninja','-S',PROJECT,'-B',BUILD,'-DMLIR_DIR='+str(LLVM/'lib/cmake/mlir'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=/usr/bin/clang','-DCMAKE_CXX_COMPILER=/usr/bin/clang++'])
        self.run('build',['cmake','--build',BUILD,'-j','2'])
    def observe(self):
        self.run('valid-input',[BUILD/'my-opt',PROJECT/'input.mlir'])
        repro=self.out/'reproducer.mlir'
        r=self.run('failure',[BUILD/'my-opt',PROJECT/'input.mlir',"--pass-pipeline=builtin.module(canonicalize,my-reject-marked-mul)",'--mlir-disable-threading','--mlir-print-ir-before-all','--mlir-print-ir-after-failure','--mlir-pass-pipeline-crash-reproducer='+str(repro),'--mlir-pass-pipeline-local-reproducer','--mlir-timing','--mlir-pass-statistics'],1)
        for anchor in ['teaching restriction: marked multiply is unsupported','IR Dump Before','IR Dump After','1 multiplications','Execution time report']:
            self.check(anchor,anchor in r.stderr)
        self.check('local-reproducer',repro.exists() and 'builtin.module(my-reject-marked-mul)' in repro.read_text() and '%dead' not in repro.read_text())
        r=self.run('replay',[BUILD/'my-opt',repro,'--run-reproducer'],1)
        self.check('same-failure','teaching restriction: marked multiply is unsupported' in r.stderr)
        r=self.run('instrument',[BUILD/'trace',PROJECT/'input.mlir'],1)
        self.check('instrument-order',all(x in r.stderr for x in ['before canonicalize operations=12','after canonicalize','before my-reject-marked-mul operations=10','failed my-reject-marked-mul']) and 'after my-reject-marked-mul' not in r.stderr)
        reduced=self.out/'reduced.mlir'
        self.run('reduce',[LLVM/'bin/mlir-reduce',PROJECT/'input.mlir','--reduction-tree=traversal-mode=0 test='+str(PROJECT/'interesting.py'),'-o',reduced])
        text=reduced.read_text();self.check('irrelevant-functions-removed','@noise' not in text and '@other' not in text and '@hit' in text)
        self.check('size-reduced',len(text)<len((PROJECT/'input.mlir').read_text()))
        self.run('reduced-valid',[BUILD/'my-opt',reduced]);self.run('interesting',[PROJECT/'interesting.py',reduced],1)
        p=self.out/'unmarked.mlir';p.write_text(text.replace(' {my.trigger}',''))
        self.run('not-interesting',[PROJECT/'interesting.py',p])
        p=self.out/'syntax-error.mlir';p.write_text('not valid IR')
        self.run('unrelated-failure',[PROJECT/'interesting.py',p])
        self.run('lit',['python3',WORKSPACE/'upstream/llvm-project/llvm/utils/lit/lit.py','-v',PROJECT/'tests'])
        self.run('lsp',['python3',PROJECT/'lsp_probe.py'])
