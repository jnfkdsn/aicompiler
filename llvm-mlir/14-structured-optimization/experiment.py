"""Real affine/structured transformations and native coordinate checks."""
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
BUILD=WORKSPACE/'artifacts/builds/mlir-structured-docs'
INSPECT=BUILD/'inspect-dependence'
FUSE=['--linalg-fuse-elementwise-ops','--canonicalize']
BUFFER=['--one-shot-bufferize=bufferize-function-boundaries function-boundary-type-conversion=identity-layout-map','--cse','--canonicalize','--buffer-deallocation-pipeline']
LOWER=['--convert-bufferization-to-memref','--convert-linalg-to-loops','--expand-strided-metadata','--lower-affine','--convert-scf-to-cf','--convert-to-llvm','--reconcile-unrealized-casts']

def log_directory():
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    p=WORKSPACE/'artifacts/logs/mlir-docs'/(stamp+'-structured');p.mkdir(parents=True);return p

def schedule(name):
    return ['--transform-preload-library=transform-library-paths='+str(PROJECT/(name+'.mlir')),'--transform-interpreter','--cse','--canonicalize']

class Experiment:
    def __init__(self,out,show=False):self.output,self.show,self.checks=out,show,[]
    def check(self,name,condition):self.checks.append({'name':name,'passed':bool(condition)})
    def run(self,name,command,expected=0):
        command=list(map(str,command));r=subprocess.run(command,capture_output=True,text=True,timeout=60)
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
    def build(self):
        for name,command in [('configure',['cmake','-G','Ninja','-S',PROJECT,'-B',BUILD,
            '-DMLIR_DIR='+str(LLVM/'lib/cmake/mlir'),'-DLLVM_DIR='+str(LLVM/'lib/cmake/llvm'),'-DCMAKE_BUILD_TYPE=Release']),
            ('build',['cmake','--build',BUILD,'-j','2'])]:
            if self.run(name,command).returncode:raise RuntimeError(name)
    def stage(self,kind):
        if kind=='affine-tile':source='affine-add';flags=['--affine-loop-tile=tile-sizes=2,3']
        else:
            source='elementwise';flags={'base':[],'fused':FUSE,'tiled':FUSE+schedule('tile'),'swapped':FUSE+schedule('interchange')}[kind]
        return self.artifact(kind,[OPT,PROJECT/(source+'.mlir'),*flags,'--verify-each'])
    def native(self):
        objects=[]
        for name,original,kind in [('crop','crop',None),('triangle','triangle',None),('affine_add','affine-add',None),
            ('affine_tiled','affine-add','affine-tile'),('wave','wave',None),('wave_wrong','wave','wrong'),
            *(("elementwise_"+k,'elementwise',k) for k in ['base','fused','tiled','swapped'])]:
            if kind=='wrong':
                text=(PROJECT/'wave.mlir').read_text().replace('affine.for %i = 1 to 5 {\n      affine.for %j = 0 to 6 {',
                    'affine.for %j = 0 to 6 {\n      affine.for %i = 1 to 5 {')
            elif kind is not None:text=self.stage(kind).read_text()
            else:text=(PROJECT/(original+'.mlir')).read_text()
            text=text.replace('@'+original.replace('-','_')+'(', '@'+name+'(')
            p=self.output/(name+'-input.mlir');p.write_text(text)
            prefix=BUFFER if original=='elementwise' else []
            lowered=self.artifact(name+'-llvm',[OPT,p,*prefix,*LOWER,'--verify-each'])
            ll=self.artifact(name+'-translate',[LLVM/'bin/mlir-translate',lowered,'--mlir-to-llvmir'],'.ll')
            obj=self.output/(name+'.o');objects.append(obj)
            if self.run(name+'-codegen',[LLVM/'bin/llc','-O0','-filetype=obj','-relocation-model=pic',ll,'-o',obj]).returncode:raise RuntimeError('codegen')
        exe=self.output/'driver'
        if self.run('link',['/usr/bin/clang','-std=c11','-Wall','-Wextra','-Werror',PROJECT/'driver.c',*objects,
            '-L'+str(LLVM/'lib'),'-lmlir_c_runner_utils','-Wl,-rpath,'+str(LLVM/'lib'),'-o',exe]).returncode:raise RuntimeError('link')
        r=self.run('execute',[exe]);rows=[]
        for line in r.stdout.splitlines():
            f=line.split('\t');rows.append(f)
            if f[0]=='case':self.check('native-'+f[1],int(f[3])==0)
        self.check('native-case-count',sum(r[0]=='case' for r in rows)==33)
        (self.output/'observations.json').write_text(json.dumps(rows,indent=2)+'\n');return rows
