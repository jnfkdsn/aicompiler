"""Vector representations, Transform scheduling and native observations."""
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
LOWER=['--lower-vector-mask','--convert-vector-to-scf','--convert-vector-to-llvm',
    '--convert-linalg-to-loops','--expand-strided-metadata','--lower-affine',
    '--convert-scf-to-cf','--convert-to-llvm','--reconcile-unrealized-casts']
CODEGEN=['-O3','-mtriple=x86_64-pc-linux-gnu','-mcpu=x86-64','-relocation-model=pic']

def log_directory():
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    p=WORKSPACE/'artifacts/logs/mlir-docs'/(stamp+'-vector');p.mkdir(parents=True);return p

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
    def automatic(self):
        return self.artifact('automatic-vector',[OPT,PROJECT/'elementwise.mlir',*schedule('vectorize'),'--verify-each'])
    def lower(self,name,source,patterns=False):
        return self.artifact(name+'-llvm',[OPT,source,*(schedule('lower-vectors') if patterns else []),*LOWER,'--verify-each'])
    def objects(self):
        objects=[]
        for name,source in [('scalar',PROJECT/'elementwise.mlir'),('automatic',self.automatic()),
            *((n,PROJECT/(n+'.mlir')) for n in ['transfer','masked','split','values','reduction'])]:
            txt=source.read_text()
            if name in ['scalar','automatic']:txt=txt.replace('@elementwise(', '@'+name+'(')
            p=self.output/(name+'-input.mlir');p.write_text(txt)
            lowered=self.lower(name,p,patterns=name in ['values','reduction'])
            ll=self.artifact(name+'-translate',[LLVM/'bin/mlir-translate',lowered,'--mlir-to-llvmir'],'.ll')
            obj=self.output/(name+'.o');objects.append(obj)
            if self.run(name+'-codegen',[LLVM/'bin/llc',*CODEGEN,'-filetype=obj',ll,'-o',obj]).returncode:raise RuntimeError('codegen')
            self.run(name+'-asm',[LLVM/'bin/llc',*CODEGEN,ll,'-o',self.output/(name+'.s')])
        return objects
    def native(self,benchmark=True):
        objects=self.objects()
        for name in ['driver',*(['benchmark'] if benchmark else [])]:
            exe=self.output/name
            if self.run(name+'-link',['/usr/bin/clang','-O2','-std=c11','-Wall','-Wextra','-Werror',
                PROJECT/(name+'.c'),*objects,'-lm','-o',exe]).returncode:raise RuntimeError('link')
            r=self.run(name+'-execute',[exe])
            rows=[l.split('\t') for l in r.stdout.splitlines()]
            (self.output/(name+'-observations.json')).write_text(json.dumps(rows,indent=2)+'\n')
            for row in rows:
                if row[0]=='case':self.check('native-'+row[1],row[3]=='0')
            if name=='driver':self.check('native-case-count',sum(row[0]=='case' for row in rows)==59)
        self.run('host',['/usr/bin/lscpu'])
