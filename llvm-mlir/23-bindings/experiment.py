from datetime import datetime
import os
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
BUILD=WORKSPACE/'artifacts/builds/mlir-bindings'
PYTHON=WORKSPACE/'artifacts/venvs/mlir-python20/bin/python'
PACKAGE=LLVM/'tools/mlir/python_packages/mlir_core'
def log_directory():
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')+'-bindings')
    out.mkdir(parents=True);return out
class Experiment:
    def __init__(self,out,show=False):self.out,self.show,self.checks=out,show,[]
    def check(self,name,ok):self.checks.append({'name':name,'passed':bool(ok)})
    def run(self,name,cmd,expected=0,python=False):
        env=os.environ.copy()
        if python:env['PYTHONPATH']=str(PACKAGE)
        cmd=list(map(str,cmd));r=subprocess.run(cmd,capture_output=True,text=True,timeout=180,env=env)
        display=('PYTHONPATH='+shlex.quote(str(PACKAGE))+' ' if python else '')+shlex.join(cmd)
        for suffix,text in [('command.txt',display+'\n'),('stdout.txt',r.stdout),('stderr.txt',r.stderr)]:
            (self.out/(name+'.'+suffix)).write_text(text)
        self.check(name,r.returncode==expected)
        if self.show or r.returncode!=expected:print('$ '+display+'\n'+r.stdout+r.stderr)
        return r
    def build(self):
        self.run('configure',['cmake','-G','Ninja','-S',PROJECT,'-B',BUILD,'-DMLIR_DIR='+str(LLVM/'lib/cmake/mlir'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=/usr/bin/clang','-DCMAKE_CXX_COMPILER=/usr/bin/clang++'])
        self.run('build',['cmake','--build',BUILD,'-j','2'])
    def observe(self):
        c=self.run('c',[BUILD/'c-api'])
        py=self.run('python',[PYTHON,PROJECT/'bindings.py'],python=True)
        self.check('same-results',c.stdout==py.stdout)
        for name,r in [('c',c),('python',py)]:
            before,after=r.stdout.split('after replacement:')
            self.check(name+'-fold','arith.constant 42' in before and 'arith.addi' not in before)
            self.check(name+'-replace','arith.constant 7' in after and 'arith.constant 42' not in after)
            for stage,source in [('fold',before.split('after fold:')[1]),('replace',after)]:
                p=self.out/(name+'-'+stage+'.mlir');p.write_text(source)
                self.run(name+'-'+stage+'-verify',[LLVM/'bin/mlir-opt',p])
        life=self.run('lifetime',[PYTHON,PROJECT/'lifetime.py'],python=True)
        self.check('erase-invalidated','the operation has been invalidated' in life.stdout)
        self.check('context-retained','module survives default-context scope: True' in life.stdout)
        errors=self.run('errors',[PYTHON,PROJECT/'errors.py'],python=True)
        self.check('parse-failure','parse rejected: MLIRError' in errors.stdout)
        self.check('pipeline-failure','pipeline rejected: ValueError' in errors.stdout)
