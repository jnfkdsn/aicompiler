"""Compile Matmul schedules and two Attention storage organizations for CPU."""
from datetime import datetime
import json
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
LLVM=WORKSPACE/'artifacts/builds/mlir-20.1.8'
OPT=LLVM/'bin/mlir-opt'
LOWER=['--convert-linalg-to-loops','--expand-strided-metadata','--lower-affine',
       '--convert-scf-to-cf','--convert-math-to-libm','--convert-to-llvm','--reconcile-unrealized-casts']

def log_directory():
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(stamp+'-attention');out.mkdir(parents=True);return out

class Experiment:
    def __init__(self, output, show=False):
        self.output, self.show, self.checks = output, show, []

    def check(self, name, condition):
        self.checks.append({'name': name, 'passed': bool(condition)})

    def run(self, name, command, expected=0):
        command = list(map(str, command))
        r = subprocess.run(command, capture_output=True, text=True, timeout=120)
        for suffix, content in [('command.txt', shlex.join(command) + '\n'),
                                ('stdout.txt', r.stdout), ('stderr.txt', r.stderr)]:
            (self.output / (name + '.' + suffix)).write_text(content)
        self.checks.append({'name': name, 'command': command, 'returncode': r.returncode,
                            'expected': expected, 'passed': r.returncode == expected})
        if self.show or r.returncode != expected:
            print('$ ' + shlex.join(command), flush=True)
            print(r.stdout, end='')
            print(r.stderr, end='')
        return r

    def artifact(self, name, command, suffix='.mlir'):
        r = self.run(name, command)
        if r.returncode:
            raise RuntimeError(name + ' failed; see logs')
        path = self.output / (name + suffix)
        path.write_text(r.stdout)
        return path

    def scheduled(self, name):
        return self.artifact(name+'-scheduled',[OPT,PROJECT/'matmul.mlir',
            '--transform-preload-library=transform-library-paths='+str(PROJECT/(name+'.mlir')),
            '--transform-interpreter','--canonicalize','--verify-each'])
    def objects(self, bad_online=False):
        objects=[]
        for name, source in [('matmul',PROJECT/'matmul.mlir'),('tiled',self.scheduled('tile')),
                ('unrolled',self.scheduled('unroll')),('attention',PROJECT/'attention.mlir'),('online',PROJECT/'online.mlir')]:
            code=source.read_text()
            if name in ['tiled','unrolled']:code=code.replace('@matmul(', '@'+name+'(')
            if name=='online' and bad_online:
                code=code.replace('%rescaled = arith.mulf %alpha, %old', '%rescaled = arith.addf %zero, %old')
            src=self.output/(name+'-input.mlir');src.write_text(code)
            low=self.artifact(name+'-llvm',[OPT,src,*LOWER,'--verify-each'])
            ll=self.artifact(name+'-translate',[LLVM/'bin/mlir-translate',low,'--mlir-to-llvmir'],'.ll')
            obj=self.output/(name+'.o')
            if self.run(name+'-codegen',[LLVM/'bin/llc','-O2','-filetype=obj','-relocation-model=pic',ll,'-o',obj]).returncode:raise RuntimeError('codegen')
            objects.append(obj)
        return objects
    def native(self, bad_online=False):
        objects=self.objects(bad_online)
        exe=self.output/'driver'
        if self.run('link',['/usr/bin/clang','-O2','-std=c11','-Wall','-Wextra','-Werror',PROJECT/'driver.c',*objects,'-lm','-o',exe]).returncode:raise RuntimeError('link')
        r=self.run('execute',[exe],expected=int(bad_online))
        rows=[line.split('\t') for line in r.stdout.splitlines()]
        (self.output/'observations.json').write_text(json.dumps(rows,indent=2)+'\n')
        if not bad_online:
            for row in rows:
                if row[0]!='value':self.check('numeric-'+'-'.join(row[:3]),row[-1]=='1')
        self.check('numeric-count',sum(row[0]!='value' for row in rows)==48)
        return rows
