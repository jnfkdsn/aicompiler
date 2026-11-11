"""Observe consumer queries, shape rewriting and tensor-to-buffer decisions."""
from datetime import datetime
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
BUILD=WORKSPACE/'artifacts/builds/mlir-extension-interfaces'
OPT=LLVM/'bin/mlir-opt'

def log_directory():
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')+'-interfaces')
    out.mkdir(parents=True);return out

class Experiment:
    def __init__(self,out,show=False):self.out,self.show,self.checks=out,show,[]
    def check(self,name,ok):self.checks.append({'name':name,'passed':bool(ok)})
    def run(self,name,cmd,expected=0):
        cmd=list(map(str,cmd));r=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
        for suffix,value in [('command.txt',shlex.join(cmd)+'\n'),('stdout.txt',r.stdout),('stderr.txt',r.stderr)]:
            (self.out/(name+'.'+suffix)).write_text(value)
        self.check(name,r.returncode==expected)
        if self.show or r.returncode!=expected:print('$ '+shlex.join(cmd)+'\n'+r.stdout+r.stderr,flush=True)
        return r
    def artifact(self,name,cmd,suffix='.mlir'):
        r=self.run(name,cmd)
        if r.returncode:raise RuntimeError(name)
        p=self.out/(name+suffix);p.write_text(r.stdout);return p
    def build(self):
        self.run('configure',['cmake','-G','Ninja','-S',PROJECT,'-B',BUILD,'-DMLIR_DIR='+str(LLVM/'lib/cmake/mlir'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=/usr/bin/clang','-DCMAKE_CXX_COMPILER=/usr/bin/clang++'])
        self.run('build',['cmake','--build',BUILD,'-j','2'])
    def buffer(self):
        self.artifact('analysis',[BUILD/'my-opt',PROJECT/'bufferization.mlir','--one-shot-bufferize=test-analysis-only print-conflicts'])
        converted=self.artifact('bufferized',[BUILD/'my-opt',PROJECT/'bufferization.mlir','--one-shot-bufferize','--canonicalize'])
        reuse,preserve=converted.read_text().split('func.func @preserve')
        self.check('reuse-no-allocation','memref.alloc' not in reuse)
        self.check('preserve-allocation',preserve.count('memref.alloc')==1)
        self.check('full-overwrite-no-copy','memref.copy' not in converted.read_text())
        self.check('no-custom-or-tensor','my.add_one' not in converted.read_text() and 'tensor<' not in converted.read_text())
        owned=self.artifact('ownership',[OPT,converted,'--buffer-deallocation-pipeline'])
        self.check('one-free',owned.read_text().count('memref.dealloc')==1)
        lowered=self.artifact('llvm',[OPT,owned,'--convert-scf-to-cf','--convert-to-llvm','--reconcile-unrealized-casts'])
        translated=self.artifact('translate',[LLVM/'bin/mlir-translate',lowered,'--mlir-to-llvmir'],'.ll')
        obj=self.out/'buffer.o';exe=self.out/'driver'
        self.run('codegen',[LLVM/'bin/llc','-filetype=obj','-relocation-model=pic',translated,'-o',obj])
        self.run('link',['/usr/bin/clang','-std=c11','-Wall','-Wextra','-Werror',PROJECT/'driver.c',obj,'-o',exe])
        r=self.run('native',[exe]);self.check('four-native',len(r.stdout.splitlines())==4 and all(x.endswith('preserved=1') for x in r.stdout.splitlines()))
        missing=self.run('missing-model',[BUILD/'my-opt-no-buffer',PROJECT/'bufferization.mlir','--one-shot-bufferize'],1)
        self.check('missing-diagnostic','op was not bufferized' in missing.stderr)
        unknown=self.artifact('unknown-boundary',[BUILD/'my-opt-no-buffer',PROJECT/'bufferization.mlir','--one-shot-bufferize=allow-unknown-ops','--canonicalize'])
        self.check('unknown-still-present','my.add_one' in unknown.read_text())
    def shape(self):
        r=self.run('infer',[BUILD/'my-opt',PROJECT/'shape.mlir','--my-probe-interfaces'])
        self.check('dynamic-infer','inferred result: tensor<?xf32>' in r.stderr)
        self.check('static-infer','inferred result: tensor<4xf32>' in r.stderr)
        shape=self.artifact('reified',[BUILD/'my-opt',PROJECT/'shape.mlir','--resolve-ranked-shaped-type-result-dims','--canonicalize'])
        self.check('dim-input','tensor.dim %arg0' in shape.read_text())
        self.check('static-four','arith.constant 4 : index' in shape.read_text())
        self.check('dead-compute-gone','my.add_one' not in shape.read_text())
    def control(self):
        r=self.run('interfaces',[BUILD/'my-opt',PROJECT/'control.mlir','--my-probe-interfaces'])
        for anchor in ['call func.call arguments=2 resolved=1','scf.for from parent: region0[1] parent[1]','scf.if from parent: region0[0] region1[0]','loop scf.for regions=1']:
            self.check(anchor,anchor in r.stderr)
        p=self.artifact('control-simplified',[BUILD/'my-opt',PROJECT/'control.mlir','--inline','--sccp','--canonicalize'])
        self.check('constant-through-call','arith.constant 7 : i32' in p.read_text() and 'call @' not in p.read_text() and 'scf.if' not in p.read_text())

        scope=self.artifact('scope-sccp',[BUILD/'my-opt',PROJECT/'scope.mlir','--my-probe-interfaces','--sccp','--canonicalize'])
        self.check('scope-result-seven','arith.constant 7 : i32' in scope.read_text() and 'my.scope' not in scope.read_text())
        notes=(self.out/'scope-sccp.stderr.txt').read_text()
        for anchor in ['my.scope from parent: region0[1]','my.scope from region: parent[1]','region-kind my.scope[0] SSA=1','region-kind builtin.module[0] SSA=0']:
            self.check(anchor,anchor in notes)
