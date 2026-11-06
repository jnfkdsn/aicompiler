"""Observe GPU lowering and finite dependency models; never runs device kernels."""
from datetime import datetime
import json
from pathlib import Path
import re
import shlex
import subprocess
from zoneinfo import ZoneInfo
from models import observations

PROJECT = Path(__file__).resolve().parent
WORKSPACE = PROJECT.parents[2]
LLVM = WORKSPACE / 'artifacts/builds/mlir-20.1.8'
OPT = LLVM / 'bin/mlir-opt'
NVVM = 'builtin.module(convert-scf-to-cf,gpu.module(convert-gpu-to-nvvm,reconcile-unrealized-casts))'
HOST = 'builtin.module(convert-scf-to-cf,gpu.module(convert-gpu-to-nvvm,reconcile-unrealized-casts),gpu-to-llvm,reconcile-unrealized-casts)'


def log_directory():
    stamp = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    out = WORKSPACE / 'artifacts/logs/mlir-docs' / (stamp + '-gpu')
    out.mkdir(parents=True)
    return out


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

    def mapping(self):
        parallel = self.artifact('parallel-mapped', [OPT, PROJECT / 'parallel.mlir',
            '--gpu-map-parallel-loops', '--convert-parallel-loops-to-gpu', '--verify-each'])
        forall = self.artifact('forall-mapped', [OPT, PROJECT / 'forall.mlir',
            '--transform-preload-library=transform-library-paths=' + str(PROJECT / 'map-forall.mlir'),
            '--transform-interpreter', '--canonicalize', '--verify-each'])
        return parallel, forall

    def outlining(self, name='launch'):
        return self.artifact(name + '-outlined', [OPT, PROJECT / (name + '.mlir'),
            '--gpu-kernel-outlining', '--verify-each'])

    def lowering(self):
        outputs = {}
        for name in ['launch', 'async', 'shared']:
            source = PROJECT / 'shared.mlir' if name == 'shared' else self.outlining(name)
            outputs[name] = self.artifact(name + '-nvvm', [OPT, source,
                '--pass-pipeline=' + NVVM, '--verify-each'])
        outputs['host'] = self.artifact('async-host', [OPT, self.outlining('async'),
            '--pass-pipeline=' + HOST, '--verify-each'])
        return outputs

    def models(self):
        data = observations()
        (self.output / 'models.json').write_text(json.dumps(data, indent=2) + '\n')
        if self.show:
            small = {**data, 'coverage': [r for r in data['coverage'] if r['n'] == 10 and r['block'] == 4]}
            print(json.dumps(small, indent=2))
        return data

    def serialize(self):
        # This path needs an LLVM build with NVPTX; assembly needs CUDA ptxas.
        pipeline = '--gpu-lower-to-nvvm-pipeline=cubin-chip=sm_80 cubin-features=+ptx70 cubin-format=isa opt-level=2'
        outputs = {}
        for name in ['async', 'shared']:
            binary = self.artifact(name + '-binary', [OPT, PROJECT / (name + '.mlir'),
                pipeline, '--verify-each'])
            # MLIR prints PTX as one quoted string with byte escapes.
            strings = re.findall(r'"((?:[^"\\]|\\.)*)"', binary.read_text())
            encoded = next(s for s in strings if '.version' in s and '.target' in s)
            ptx = re.sub(r'\\([0-9A-Fa-f]{2})', lambda m: chr(int(m[1], 16)), encoded)
            ptx = ptx.replace('\\"', '"').replace('\\\\', '\\')
            path = self.output / (name + '.ptx')
            path.write_text(ptx)
            cubin = self.output / (name + '.cubin')
            self.run(name + '-ptxas', ['/usr/local/cuda/bin/ptxas', '-arch=sm_80',
                '-v', path, '-o', cubin])
            outputs[name] = {'binary': binary, 'ptx': path, 'cubin': cubin}
        host = self.artifact('host-translated', [LLVM / 'bin/mlir-translate',
            outputs['async']['binary'], '--mlir-to-llvmir'], '.ll')
        self.run('host-object', [LLVM / 'bin/llc', '-mtriple=x86_64-pc-linux-gnu',
            '-relocation-model=pic', '-filetype=obj', host, '-o', self.output / 'host.o'])
        self.run('host-symbols', ['nm', '-u', self.output / 'host.o'])
        outputs['host'] = host
        return outputs
