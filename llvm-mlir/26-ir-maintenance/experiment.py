from datetime import datetime
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo
from reading_source import inspect
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
BUILD=WORKSPACE/'artifacts/builds/mlir-ir-maintenance'
def log_directory():
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')+'-ir-maintenance')
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
    def ir(self,name,file,flags=(),expected=0):
        r=self.run(name,[LLVM/'bin/mlir-opt',file,*flags],expected)
        if expected==0:(self.out/(name+'.mlir')).write_text(r.stdout)
        return r
    def build(self):
        self.run('configure',['cmake','-G','Ninja','-S',PROJECT,'-B',BUILD,'-DMLIR_DIR='+str(LLVM/'lib/cmake/mlir'),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_COMPILER=/usr/bin/clang','-DCMAKE_CXX_COMPILER=/usr/bin/clang++'])
        self.run('build',['cmake','--build',BUILD,'-j','2'])
    def observe(self):
        r=self.run('maintenance',[BUILD/'inspect',PROJECT/'maintenance.mlir'])
        for anchor in ['renamed call: renamed','clone blocks=4','clone values and CFG remapped=1','nested capture remapped=1','clone symbol reference still=leaf','bad move rejected=1','repair verifies=1','memref.alloca allocate resource=AutomaticAllocationScope stage=0 full=1','memref.copy read resource=<Default> stage=0 full=1','memref.copy write resource=<Default> stage=0 full=1','synthetic protocol read-stage=0 write-stage=1 resource=TeachingCounter','unknown symbol uses known=0','guarded rename refused=1 name-preserved=1']:
            self.check(anchor,anchor in r.stdout)
        self.check('dominance-diagnostic','does not dominate this use' in r.stderr)
        p=self.out/'maintained.mlir';p.write_text(r.stdout.split('final module:\n')[1]);self.ir('maintained-valid',p)
        r=self.ir('regions-cf',PROJECT/'scf_regions.mlir',['--convert-scf-to-cf'])
        self.check('cf-block-merge','cf.switch' in r.stdout and 'scf.' not in r.stdout and '^bb4(' in r.stdout)
        self.check('fixed-i32-selector','index to i32' in r.stdout)
        r=self.ir('unsupported-bufferize',PROJECT/'scf_regions.mlir',['--one-shot-bufferize=bufferize-function-boundaries'],1)
        self.check('unique-yield-required','without unique scf.yield is not supported' in r.stderr)
        llvmflags=['--convert-arith-to-llvm','--convert-func-to-llvm','--convert-cf-to-llvm','--reconcile-unrealized-casts']
        self.ir('regions-llvm',self.out/'regions-cf.mlir',llvmflags)
        self.ir('parallel-buffer',PROJECT/'scf_parallel.mlir',['--one-shot-bufferize=bufferize-function-boundaries','--buffer-deallocation-pipeline'])
        r=self.ir('parallel-llvm',self.out/'parallel-buffer.mlir',['--expand-strided-metadata','--lower-affine','--convert-scf-to-cf','--finalize-memref-to-llvm',*llvmflags])
        self.check('parallel-fully-lowered','scf.' not in r.stdout and 'tensor.' not in r.stdout and 'memref.' not in r.stdout)
        objects=[]
        for name in ['regions','parallel']:
            ll=self.out/(name+'.ll');obj=self.out/(name+'.o')
            self.run(name+'-translate',[LLVM/'bin/mlir-translate','--mlir-to-llvmir',self.out/(name+'-llvm.mlir'),'-o',ll])
            self.run(name+'-object',[LLVM/'bin/llc',ll,'-filetype=obj','-relocation-model=pic','-o',obj]);objects.append(obj)
        exe=self.out/'native';self.run('link',['/usr/bin/clang',*objects,PROJECT/'driver.c','-O2','-o',exe])
        r=self.run('native',[exe]);self.check('17-correct-cases',sum('expected=' in line for line in r.stdout.splitlines())==17)
        self.check('known-wide-tag-limitation','known limitation: wide tag=4294967296 observed=7 source-default=6' in r.stdout)
        r=self.ir('source-fold',PROJECT/'source_add.mlir',['--canonicalize'])
        zero=r.stdout.split('func.func @general')[0];self.check('source-zero-eliminated','arith.addi' not in zero and 'arith.constant' not in zero)
        self.check('source-general-retained','arith.addi' in r.stdout)
        r=self.ir('source-llvm',PROJECT/'source_add.mlir',['--canonicalize',*llvmflags]);self.check('source-llvm-add','llvm.add' in r.stdout and 'arith.addi' not in r.stdout)
        chain=inspect(self.out,self.show);self.check('seven-source-stages',len(chain)==7)
