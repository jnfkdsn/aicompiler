"""Pinned commands and observable execution for the memory chapters."""
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
BUFFER_FLAGS = ['--one-shot-bufferize=bufferize-function-boundaries function-boundary-type-conversion=identity-layout-map']
LOWER_FLAGS = ['--convert-bufferization-to-memref', '--convert-linalg-to-loops',
               '--expand-strided-metadata', '--lower-affine', '--convert-scf-to-cf',
               '--convert-to-llvm', '--reconcile-unrealized-casts']
BUFFER_EXAMPLES = {'reuse', 'preserve', 'readonly', 'fill-preserve', 'signature', 'tile-update'}
OWNERSHIP_EXAMPLES = {'call', 'return-alias', 'branch'}


def log_directory():
    stamp = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    out = WORKSPACE / 'artifacts/logs/mlir-docs' / (stamp + '-memory')
    out.mkdir(parents=True)
    return out


def stage_flags(name, stage):
    if stage == 'input':
        return []
    if stage == 'analysis':
        if name not in BUFFER_EXAMPLES:
            raise ValueError('analysis applies to the tensor examples')
        return [BUFFER_FLAGS[0] + ' test-analysis-only print-conflicts']
    if stage == 'buffer':
        if name not in BUFFER_EXAMPLES:
            raise ValueError('buffer applies to the tensor examples')
        return BUFFER_FLAGS + (['--cse', '--canonicalize'] if name == 'tile-update' else [])
    if stage in ('ownership', 'dealloc'):
        if name not in BUFFER_EXAMPLES | OWNERSHIP_EXAMPLES:
            raise ValueError('automatic deallocation applies to the automatic-lifetime examples')
        before = BUFFER_FLAGS if name in BUFFER_EXAMPLES else []
        return before + ['--ownership-based-buffer-deallocation' if stage == 'ownership'
                         else '--buffer-deallocation-pipeline']
    raise ValueError(stage)


class Commands:
    def __init__(self, output, show=False):
        self.output, self.show, self.checks = output, show, []

    def check(self, name, ok):
        self.checks.append({'name': name, 'passed': bool(ok)})

    def run(self, name, command, expected=0):
        command = [str(x) for x in command]
        if self.show:
            print('$ ' + shlex.join(command), flush=True)
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        for suffix, content in [('command.txt', shlex.join(command) + '\n'),
                                ('stdout.txt', result.stdout), ('stderr.txt', result.stderr)]:
            (self.output / (name + '.' + suffix)).write_text(content)
        self.checks.append({'name': name, 'command': command, 'returncode': result.returncode,
                            'expected': expected, 'passed': result.returncode == expected})
        if self.show or result.returncode != expected:
            print(result.stdout, end='')
            print(result.stderr, end='')
        return result

    def artifact(self, name, command):
        result = self.run(name, command)
        if result.returncode:
            raise RuntimeError(f'{name} failed; inspect {self.output}')
        path = self.output / (name + '.mlir')
        path.write_text(result.stdout)
        return path

    def numeric(self):
        from numeric_cases import build_driver
        observations = []
        for suite in ('manual', 'automatic'):
            code, expected = build_driver(suite)
            source = self.output / (suite + '-input.mlir')
            source.write_text(code)
            prefix = [] if suite == 'manual' else BUFFER_FLAGS + ['--buffer-deallocation-pipeline']
            lowered = self.artifact(suite + '-llvm', [OPT, source, *prefix, *LOWER_FLAGS, '--verify-each'])
            translated = self.run(suite + '-translate', [LLVM / 'bin/mlir-translate', '--mlir-to-llvmir', lowered])
            if translated.returncode:
                raise RuntimeError('LLVM translation failed')
            ir = self.output / (suite + '.ll')
            ir.write_text(translated.stdout)
            obj, exe = self.output / (suite + '.o'), self.output / suite
            result = self.run(suite + '-codegen', [LLVM / 'bin/llc', '-filetype=obj',
                '-relocation-model=pic', '-O0', ir, '-o', obj])
            if result.returncode:
                raise RuntimeError('Object generation failed')
            result = self.run(suite + '-link', ['/usr/bin/clang', obj, '-L' + str(LLVM / 'lib'),
                '-lmlir_c_runner_utils', '-Wl,-rpath,' + str(LLVM / 'lib'), '-o', exe])
            if result.returncode:
                raise RuntimeError('Native link failed')
            result = self.run(suite + '-execute', [exe])
            lines = result.stdout.splitlines()
            self.check(suite + '-observation-count', len(lines) == len(expected))
            for i, item in enumerate(expected):
                try:
                    actual = int(lines[i])
                except (ValueError, IndexError):
                    actual = None
                self.check(suite + '-' + item['name'], actual == item['expected'])
                observations.append({'suite': suite, **item, 'actual': actual})
        (self.output / 'observations.json').write_text(json.dumps(observations, ensure_ascii=False, indent=2) + '\n')
        return observations
