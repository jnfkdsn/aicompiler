"""Show group boundaries, arithmetic expansion and owned parameter storage."""
from datetime import datetime
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
BUILD=WORKSPACE/'artifacts/builds/mlir-ods-storage'
def log_directory():
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')+'-ods-storage')
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
        args=[BUILD/'my-opt',PROJECT/'input.mlir']
        r=self.run('groups',[*args,'--my-inspect-segments','--my-lower-sums','--canonicalize'])
        for anchor in ['weighted groups=2,2,1','weighted groups=0,0,0','nested groups: 2 1 0','properties={operandSegmentSizes = array<i32: 2, 2, 1>} discardable={my.note = "example"}']:
            self.check(anchor,anchor in r.stderr)
        self.check('value-32','arith.constant 32 : i32' in r.stdout)
        self.check('values-5-4-0','return %c5_i32, %c4_i32, %c0_i32' in r.stdout)
        self.check('all-expanded','my.weighted_sum' not in r.stdout and 'my.group_sum' not in r.stdout)
        r=self.run('append',[*args,'--my-append-pair','--my-inspect-segments','--my-lower-sums','--canonicalize'])
        self.check('append-sizes','array<i32: 3, 3, 1>' in r.stderr)
        self.check('append-value','arith.constant 40 : i32' in r.stdout)
        r=self.run('storage',[BUILD/'storage-probe'])
        for anchor in ['tile=!my.tile<[2, 3]> same=1 bytes=24 alignment=16 start=16 end=40','conflict_rejected=1 shared_body=1','planner capacity64=1 bounds_and_protocol_rejected=1']:
            self.check(anchor,anchor in r.stdout)
