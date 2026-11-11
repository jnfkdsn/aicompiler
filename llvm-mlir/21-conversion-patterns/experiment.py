"""Observe one-to-many boundary conversion and DRR/PDLL consumers."""
from datetime import datetime
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
BUILD=WORKSPACE/'artifacts/builds/mlir-conversion-patterns'
def log_directory():
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')+'-conversion-patterns')
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
    def artifact(self,name,cmd,suffix='.mlir'):
        r=self.run(name,cmd)
        if r.returncode:raise RuntimeError(name)
        p=self.out/(name+suffix);p.write_text(r.stdout);return p
    def build(self):
        self.run('configure',['cmake','-G','Ninja','-S',PROJECT,'-B',BUILD,'-DMLIR_DIR='+str(LLVM/'lib/cmake/mlir'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=/usr/bin/clang','-DCMAKE_CXX_COMPILER=/usr/bin/clang++'])
        self.run('build',['cmake','--build',BUILD,'-j','2'])
    def pairs(self):
        lowered=self.artifact('flatten',[BUILD/'my-opt',PROJECT/'pairs.mlir','--my-flatten-pairs'])
        text=lowered.read_text();self.check('all-pairs-eliminated','tuple<' not in text and 'my.' not in text)
        self.check('call-two-results','%0:2 = call @pair' in text)
        self.check('block-two-args','^bb1(%0: i32, %1: i32)' in text)
        llvm=self.artifact('llvm',[LLVM/'bin/mlir-opt',lowered,'--convert-to-llvm','--reconcile-unrealized-casts'])
        ir=self.artifact('translate',[LLVM/'bin/mlir-translate',llvm,'--mlir-to-llvmir'],'.ll')
        obj=self.out/'pair.o';exe=self.out/'driver'
        self.run('codegen',[LLVM/'bin/llc','-filetype=obj','-relocation-model=pic',ir,'-o',obj])
        self.run('link',['/usr/bin/clang','-std=c11','-Wall','-Wextra','-Werror',PROJECT/'driver.c',obj,'-o',exe])
        r=self.run('native',[exe]);self.check('four-native',len(r.stdout.splitlines())==4 and '20 + 22 = 42 expected 42' in r.stdout)
        r=self.run('missing-call',[BUILD/'my-opt',PROJECT/'pairs.mlir','--my-flatten-no-call'],1)
        self.check('call-diagnostic',"failed to legalize operation 'func.call'" in r.stderr)
    def patterns(self):
        pdl=self.out/'patterns.mlir'
        self.run('pdll-to-pdl',[LLVM/'bin/mlir-pdll',PROJECT/'patterns.pdll','-I',PROJECT,'-I',WORKSPACE/'upstream/llvm-project/mlir/include','-x=mlir','-o',pdl])
        self.run('pdl-parse',[LLVM/'bin/mlir-opt',pdl])
        pdltext=pdl.read_text();self.check('pattern-not-payload','pdl.pattern' in pdltext and 'apply_native_constraint "IsZero"' in pdltext and 'operation "my.add"' in pdltext)
        args=[BUILD/'my-opt',PROJECT/'rewrites.mlir']
        drr=self.artifact('drr',[*args,'--my-apply-drr'])
        pdll=self.artifact('pdll',[*args,'--my-pdl-file='+str(pdl),'--my-apply-pdl'])
        self.check('same-rule-outcome',drr.read_text()==pdll.read_text())
        right=drr.read_text().split('func.func @left')[0]
        self.check('chain-rewritten','my.add' not in right and 'return %arg0' in right)
        self.check('two-unmatched',drr.read_text().count('my.add')==2)
        plain=self.run('canonicalize-only',[*args,'--canonicalize'])
        self.check('not-standard-fold',plain.stdout.count('my.add')==4)
