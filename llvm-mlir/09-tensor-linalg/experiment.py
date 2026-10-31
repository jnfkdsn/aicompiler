"""Shared commands for observation and author validation; LLVM 20.1.8."""
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
BUFFER_FLAGS = ['--empty-tensor-to-alloc-tensor',
    '--one-shot-bufferize=bufferize-function-boundaries function-boundary-type-conversion=identity-layout-map']
LOOP_FLAGS = BUFFER_FLAGS + ['--convert-linalg-to-loops', '--lower-affine']
LLVM_FLAGS = BUFFER_FLAGS + ['--convert-linalg-to-loops', '--expand-strided-metadata',
    '--lower-affine', '--convert-scf-to-cf', '--convert-to-llvm', '--reconcile-unrealized-casts']


def log_directory(suffix='tensor-linalg'):
    stamp = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    out = WORKSPACE / 'artifacts/logs/mlir-docs' / (stamp + '-' + suffix)
    out.mkdir(parents=True)
    return out


class Commands:
    def __init__(self, output, show=False):
        self.output, self.show, self.checks = output, show, []

    def check(self, name, ok):
        self.checks.append({'name': name, 'passed': bool(ok)})

    def run(self, name, command, expected=0, timeout=60):
        command = [str(x) for x in command]
        if self.show:
            print('$ ' + shlex.join(command), flush=True)
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        for suffix, content in [('command.txt', shlex.join(command) + '\n'),
                                ('stdout.txt', result.stdout), ('stderr.txt', result.stderr)]:
            (self.output / (name + '.' + suffix)).write_text(content)
        ok = result.returncode == expected
        self.checks.append({'name': name, 'command': command, 'returncode': result.returncode,
                            'expected': expected, 'passed': ok})
        if self.show or not ok:
            print(result.stdout, end='')
            print(result.stderr, end='')
            print(f'exit={result.returncode}; expected={expected}', flush=True)
        return result

    def artifact(self, name, command):
        result = self.run(name, command)
        if result.returncode:
            raise RuntimeError(f'{name} failed; inspect {self.output}')
        path = self.output / (name + '.mlir')
        path.write_text(result.stdout)
        return path

    def numeric(self, tag='numeric', overrides=None):
        from numeric_cases import build_driver
        required = [LLVM / 'bin/llc', LLVM / 'lib/libmlir_c_runner_utils.so']
        if any(not path.is_file() for path in required):
            raise RuntimeError('Build LLVM 20.1.8 targets llc and mlir_c_runner_utils first; see README.')
        source, expected = build_driver(PROJECT, overrides)
        driver = self.output / (tag + '-input.mlir')
        driver.write_text(source)
        lowered = self.artifact(tag + '-llvm', [OPT, driver, *LLVM_FLAGS, '--verify-each'])
        translated = self.run(tag + '-translate', [LLVM / 'bin/mlir-translate', '--mlir-to-llvmir', lowered])
        if translated.returncode:
            raise RuntimeError('LLVM translation failed')
        ir = self.output / (tag + '.ll')
        ir.write_text(translated.stdout)
        obj, executable = self.output / (tag + '.o'), self.output / tag
        compiled = self.run(tag + '-codegen', [LLVM / 'bin/llc', '-filetype=obj',
            '-relocation-model=pic', '-O0', ir, '-o', obj])
        if compiled.returncode:
            raise RuntimeError('Object generation failed')
        linked = self.run(tag + '-link', ['/usr/bin/clang', obj, '-L' + str(LLVM / 'lib'),
            '-lmlir_c_runner_utils', '-Wl,-rpath,' + str(LLVM / 'lib'), '-o', executable])
        if linked.returncode:
            raise RuntimeError('Link failed')
        result = self.run(tag + '-execute', [executable])
        actual = result.stdout.splitlines()
        self.check(tag + '-observation-count', len(actual) == len(expected))
        observations = []
        for i, (item, text) in enumerate(zip(expected, actual)):
            try:
                value = float(text)
            except ValueError:
                value = None
            self.check(f'{tag}-value-{i}', value == item['expected'])
            observations.append({**item, 'actual': value})
        (self.output / (tag + '-observations.json')).write_text(
            json.dumps(observations, ensure_ascii=False, indent=2) + '\n')
        return observations
