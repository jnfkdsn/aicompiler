"""Inspect each compilation boundary and run a C ABI harness (LLVM 20.1.8)."""
from datetime import datetime
import json
from pathlib import Path
import shlex
import subprocess
from zoneinfo import ZoneInfo

PROJECT = Path(__file__).resolve().parent
WORKSPACE = PROJECT.parents[2]
LLVM = WORKSPACE / 'artifacts/builds/mlir-20.1.8'
OPT = LLVM / 'bin/mlir-opt'
LOOP_FLAGS = ['--convert-linalg-to-loops', '--lower-affine']
CF_FLAGS = LOOP_FLAGS + ['--convert-scf-to-cf']
LLVM_FLAGS = CF_FLAGS + ['--convert-to-llvm', '--reconcile-unrealized-casts']


def log_directory():
    stamp = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    out = WORKSPACE / 'artifacts/logs/mlir-docs' / (stamp + '-cpu')
    out.mkdir(parents=True)
    return out


class Commands:
    def __init__(self, output, show=False):
        self.output, self.show, self.checks = output, show, []

    def check(self, name, ok):
        self.checks.append({'name': name, 'passed': bool(ok)})

    def run(self, name, command, expected=0):
        command = [str(item) for item in command]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        for suffix, content in [('command.txt', shlex.join(command) + '\n'),
                                ('stdout.txt', result.stdout), ('stderr.txt', result.stderr)]:
            (self.output / (name + '.' + suffix)).write_text(content)
        self.checks.append({'name': name, 'command': command, 'returncode': result.returncode,
                            'expected': expected, 'passed': result.returncode == expected})
        if self.show or result.returncode != expected:
            print('$ ' + shlex.join(command), flush=True)
            print(result.stdout, end=''); print(result.stderr, end='')
        return result

    def artifact(self, name, command, extension='.mlir'):
        result = self.run(name, command)
        if result.returncode:
            raise RuntimeError(f'{name} failed; inspect {self.output}')
        path = self.output / (name + extension)
        path.write_text(result.stdout)
        return path

    def stage(self, name, stage):
        source = PROJECT / (name + '.mlir')
        flags = {'input': [], 'loops': LOOP_FLAGS, 'cf': CF_FLAGS, 'llvm': LLVM_FLAGS}[stage]
        if name == 'make-copy' and stage == 'llvm':
            flags = ['--buffer-deallocation-pipeline', *flags]
        return self.artifact(name + '-' + stage, [OPT, source, *flags, '--verify-each'])

    def native(self):
        objects = []
        for name in ('add-into', 'sum', 'read2d', 'make-copy', 'pointer', 'choose'):
            lowered = self.stage(name, 'llvm')
            ir = self.artifact(name + '-translate', [LLVM / 'bin/mlir-translate', lowered, '--mlir-to-llvmir'], '.ll')
            obj = self.output / (name + '.o')
            result = self.run(name + '-codegen', [LLVM / 'bin/llc', '-filetype=obj', '-relocation-model=pic', '-O0', ir, '-o', obj])
            if result.returncode: raise RuntimeError('Code generation failed')
            objects.append(obj)
        exe = self.output / 'driver'
        result = self.run('link-driver', ['/usr/bin/clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
            PROJECT / 'driver.c', *objects, '-L' + str(LLVM / 'lib'), '-lmlir_c_runner_utils',
            '-Wl,-rpath,' + str(LLVM / 'lib'), '-o', exe])
        if result.returncode: raise RuntimeError('C ABI link failed')
        result = self.run('execute-driver', [exe])
        observations = []
        for line in result.stdout.splitlines():
            name, actual, expected = line.split('\t')
            actual, expected = float(actual), float(expected)
            self.check('native-' + name, actual == expected)
            observations.append({'name': name, 'actual': actual, 'expected': expected})
        self.check('native-observation-count', len(observations) == 33)
        (self.output / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
        return observations
