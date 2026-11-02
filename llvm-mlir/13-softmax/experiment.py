"""Pinned scalar math and Softmax lowering, with observable numeric evidence."""
from datetime import datetime
from pathlib import Path
import json
import shlex
import subprocess
from zoneinfo import ZoneInfo

PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
OPT=LLVM/'bin/mlir-opt'
BUFFER=['--one-shot-bufferize=bufferize-function-boundaries function-boundary-type-conversion=identity-layout-map',
        '--cse','--canonicalize']
LOWER=['--convert-bufferization-to-memref','--convert-linalg-to-loops',
       '--expand-strided-metadata','--lower-affine','--convert-scf-to-cf',
       '--convert-math-to-libm','--convert-index-to-llvm','--convert-to-llvm','--reconcile-unrealized-casts']

def log_directory():
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(stamp+'-softmax');out.mkdir(parents=True)
    return out

class Experiment:
    def __init__(self,out,show=False): self.output,self.show,self.checks=out,show,[]
    def check(self,name,condition):self.checks.append({'name':name,'passed':bool(condition)})
    def run(self,name,command,expected=0):
        command=list(map(str,command))
        r=subprocess.run(command,capture_output=True,text=True,timeout=60)
        for suffix,text in [('command.txt',shlex.join(command)+'\n'),('stdout.txt',r.stdout),('stderr.txt',r.stderr)]:
            (self.output/(name+'.'+suffix)).write_text(text)
        self.checks.append({'name':name,'command':command,'returncode':r.returncode,'expected':expected,'passed':r.returncode==expected})
        if self.show or r.returncode!=expected:
            print('$ '+shlex.join(command),flush=True);print(r.stdout,end='');print(r.stderr,end='')
        return r
    def artifact(self,name,command,suffix='.mlir'):
        r=self.run(name,command)
        if r.returncode:raise RuntimeError(name+' failed')
        p=self.output/(name+suffix);p.write_text(r.stdout);return p
    def stage(self,name,stage):
        prefix=BUFFER if name=='softmax' and stage!='input' else []
        suffix=[] if stage in ('input','buffer') else ['--buffer-deallocation-pipeline',*LOWER]
        return self.artifact(name+'-'+stage,[OPT,PROJECT/(name+'.mlir'),*prefix,*suffix,'--verify-each'])
    def native(self):
        objects=[]
        for name in ['softmax','row-softmax','math','index','math-llvm']:
            if name=='math-llvm':
                source=self.output/'math-llvm-input.mlir'
                source.write_text((PROJECT/'math.mlir').read_text().replace('@','@llvm_'))
                ir=self.artifact(name+'-llvm',[OPT,source,'--convert-math-to-llvm','--convert-to-llvm','--reconcile-unrealized-casts'])
            else: ir=self.stage(name,'llvm')
            ll=self.artifact(name+'-translate',[LLVM/'bin/mlir-translate',ir,'--mlir-to-llvmir'],'.ll')
            obj=self.output/(name+'.o')
            if self.run(name+'-codegen',[LLVM/'bin/llc','-O0','-filetype=obj','-relocation-model=pic',ll,'-o',obj]).returncode:raise RuntimeError('codegen')
            objects.append(obj)
        exe=self.output/'driver'
        if self.run('link',['/usr/bin/clang','-std=c11','-Wall','-Wextra','-Werror',PROJECT/'driver.c',*objects,
            '-lm','-L'+str(LLVM/'lib'),'-lmlir_c_runner_utils','-Wl,-rpath,'+str(LLVM/'lib'),'-o',exe]).returncode:raise RuntimeError('link')
        result=self.run('execute',[exe]);rows=[]
        for line in result.stdout.splitlines():
            fields=line.split('\t');rows.append(fields)
            if fields[0]!='value':self.check('numeric-'+'-'.join(fields[:3]),fields[-1]=='1')
        self.check('softmax-case-count',sum(row[0]=='softmax' for row in rows)==20)
        self.check('numeric-record-count',len(rows)==44)
        (self.output/'observations.json').write_text(json.dumps(rows,indent=2)+'\n')
        return rows
