from datetime import datetime
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
def log_directory():
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')+'-domain-extensions')
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
    def observe(self):
        self.run('models',['python3',PROJECT/'models.py'])
        self.ir('quant',PROJECT/'quant.mlir')
        plain=self.ir('sparse-without-map',PROJECT/'sparse.mlir',['--sparsification'])
        self.check('needs-mapping','linalg.generic' in plain.stdout)
        sparse=self.ir('sparse-loops',PROJECT/'sparse.mlir',['--sparse-reinterpret-map','--sparsification'])
        for anchor in ['sparse_tensor.positions','sparse_tensor.coordinates','sparse_tensor.values','scf.for','memref.load']:
            self.check('sparse-'+anchor,anchor in sparse.stdout)
        self.check('generic-consumed','linalg.generic {' not in sparse.stdout)
        shape=self.ir('shape-fold',PROJECT/'shape.mlir',['--canonicalize'])
        self.check('broadcast-result','shape.const_shape [2, 3]' in shape.stdout)
        self.check('static-witness','shape.const_witness true' in shape.stdout)
        r=self.ir('shape-assert',PROJECT/'shape.mlir',['--pass-pipeline=builtin.module(func.func(convert-shape-constraints,canonicalize))'])
        self.check('assert-and-no-assuming','cf.assert' in r.stdout and 'shape.assuming' not in r.stdout)
        r=self.ir('dynamic',PROJECT/'dynamic.mlir',['--irdl-file='+str(PROJECT/'my.irdl.mlir'),'--canonicalize'])
        self.check('unknown-effects-retained',r.stdout.count('"my.add"')==2)
        r=self.ir('complex-arithmetic',PROJECT/'complex.mlir',['--convert-complex-to-standard','--canonicalize'])
        self.check('complex-fold','-5.000000e+00' in r.stdout and '1.000000e+01' in r.stdout)
        self.check('complex-lowering','complex.mul' not in r.stdout and 'complex.abs' not in r.stdout and 'math.sqrt' in r.stdout and 'arith.cmpf uno' in r.stdout)
        r=self.ir('tosa-linalg',PROJECT/'tosa.mlir',['--pass-pipeline=builtin.module(func.func(tosa-to-linalg))'])
        self.check('tensor-pointwise','linalg.generic' in r.stdout and 'arith.addf' in r.stdout and 'tosa.add' not in r.stdout)
