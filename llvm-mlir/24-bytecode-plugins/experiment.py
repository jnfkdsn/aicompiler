from datetime import datetime
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
BUILD=WORKSPACE/'artifacts/builds/mlir-bytecode-plugins'
def log_directory():
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')+'-bytecode-plugins')
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
        old=self.out/'old.mlirbc';new=self.out/'new.mlirbc'
        for version,output in [(1,old),(2,new)]:
            self.run('write-v'+str(version),[BUILD/f'my-opt-v{version}',PROJECT/f'v{version}.mlir','--emit-bytecode','-o',output])
            self.check('bytecode-magic-v'+str(version),output.read_bytes()[:4]==bytes.fromhex('4d4cef52'))
            self.run('self-read-v'+str(version),[BUILD/f'my-opt-v{version}',output])
        upgraded=self.run('upgrade',[BUILD/'my-opt-v2',old]);self.check('bias-to-offset','offset = 5' in upgraded.stdout and 'bias' not in upgraded.stdout)
        a=self.run('old-compute',[BUILD/'my-opt-v1',old,'--my-lower-shift','--canonicalize'])
        b=self.run('upgraded-compute',[BUILD/'my-opt-v2',old,'--my-lower-shift','--canonicalize'])
        self.check('same-computation',a.stdout==b.stdout and 'constant 42' in b.stdout)
        r=self.run('reject-new',[BUILD/'my-opt-v1',new],1);self.check('future-diagnostic','unsupported my dialect version 2 by reader 1' in r.stderr)
        r=self.run('old-text-not-upgraded',[BUILD/'my-opt-v2',PROJECT/'v1.mlir'],1);self.check('text-current-schema','version 2 requires only offset' in r.stderr)
        container=self.out/'container-v0.mlirbc'
        self.run('old-container',[BUILD/'my-opt-v2',PROJECT/'v2.mlir','--emit-bytecode','--emit-bytecode-version=0','-o',container])
        r=self.run('read-old-container',[BUILD/'my-opt-v2',container]);self.check('container-separate','offset = 5' in r.stdout)
        r=self.run('invalid-container',[BUILD/'my-opt-v2',PROJECT/'v2.mlir','--emit-bytecode','--emit-bytecode-version=999','-o',self.out/'invalid.mlirbc'],1)
        self.check('container-error','unsupported version requested 999' in r.stderr)
        r=self.run('missing-dialect',[LLVM/'bin/mlir-opt',PROJECT/'v2.mlir'],1);self.check('unknown-my',"Dialect `my' not found" in r.stderr)
        dialect='--load-dialect-plugin='+str(BUILD/'MyPlugin.so')
        passes='--load-pass-plugin='+str(BUILD/'MyPlugin.so')
        r=self.run('dialect-plugin',[LLVM/'bin/mlir-opt',PROJECT/'v2.mlir',dialect]);self.check('plugin-shift','my.shift' in r.stdout)
        r=self.run('plugin-upgrade',[LLVM/'bin/mlir-opt',old,dialect]);self.check('plugin-offset','offset = 5' in r.stdout)
        r=self.run('pass-plugin',[LLVM/'bin/mlir-opt',PROJECT/'v2.mlir',dialect,passes,'--pass-pipeline=builtin.module(my-plugin-mark)']);self.check('plugin-executed','my.plugin_seen' in r.stdout)
        r=self.run('bad-plugin',[BUILD/'plugin-check',BUILD/'BadPlugin.so'],1)
        self.check('plugin-api-error','Wrong API version' in r.stderr or 'API version' in r.stderr)
