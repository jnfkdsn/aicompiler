"""Observable MLIR analysis queries and before/after CPU execution."""
from datetime import datetime
from pathlib import Path
import json
import re
import shlex
import subprocess
from zoneinfo import ZoneInfo

PROJECT = Path(__file__).resolve().parent
WORKSPACE = PROJECT.parents[2]
LLVM = WORKSPACE / 'artifacts/builds/mlir-20.1.8'
OPT = LLVM / 'bin/mlir-opt'
BUILD = WORKSPACE / 'artifacts/builds/mlir-analysis-docs'
INSPECT = BUILD / 'inspect-analysis'
OPTIMIZE = ['--cse', '--loop-invariant-code-motion']


def log_directory():
    stamp = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    out = WORKSPACE / 'artifacts/logs/mlir-docs' / (stamp + '-analysis')
    out.mkdir(parents=True)
    return out


class Experiment:
    def __init__(self, output, show=False):
        self.output, self.show, self.checks = output, show, []

    def check(self, name, condition):
        self.checks.append({'name': name, 'passed': bool(condition)})

    def run(self, name, command, expected=0):
        command = list(map(str, command))
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        for suffix, text in [('command.txt', shlex.join(command) + '\n'),
                             ('stdout.txt', result.stdout), ('stderr.txt', result.stderr)]:
            (self.output / (name + '.' + suffix)).write_text(text)
        self.checks.append({'name': name, 'command': command, 'returncode': result.returncode,
                            'expected': expected, 'passed': result.returncode == expected})
        if self.show or result.returncode != expected:
            print('$ ' + shlex.join(command), flush=True)
            print(result.stdout, end=''); print(result.stderr, end='')
        return result

    def artifact(self, name, command, suffix='.mlir'):
        r = self.run(name, command)
        if r.returncode: raise RuntimeError(name + ' failed')
        p = self.output / (name + suffix); p.write_text(r.stdout)
        return p

    def build(self):
        for name, command in [('configure', ['cmake', '-G', 'Ninja', '-S', PROJECT, '-B', BUILD,
                '-DMLIR_DIR=' + str(LLVM/'lib/cmake/mlir'),
                '-DLLVM_DIR=' + str(LLVM/'lib/cmake/llvm'), '-DCMAKE_BUILD_TYPE=Release']),
                ('build', ['cmake', '--build', BUILD, '-j', '2'])]:
            if self.run(name, command).returncode: raise RuntimeError(name + ' failed')

    def query(self, mode, fixture, name=None):
        return self.run(name or mode, [INSPECT, mode, fixture]).stdout

    def native(self):
        # C wrappers are a calling convenience for the harness. The operation
        # semantics and the optimization candidate bodies are unchanged.
        source = re.sub(r'^(  func\.func [^\n]+ -> i32) \{',
            r'\1 attributes {llvm.emit_c_interface} {',
            (PROJECT/'optimizations.mlir').read_text(), flags=re.M)
        p = self.output/'native-input.mlir'; p.write_text(source)
        outputs = {}
        for label, flags in [('before', []), ('after', OPTIMIZE)]:
            transformed = self.artifact(label, [OPT, p, *flags, '--verify-each'])
            lowered = self.artifact(label+'-llvm', [OPT, transformed, '--convert-scf-to-cf',
                '--convert-to-llvm', '--reconcile-unrealized-casts', '--verify-each'])
            ir = self.artifact(label+'-translate', [LLVM/'bin/mlir-translate', lowered, '--mlir-to-llvmir'], '.ll')
            obj = self.output/(label+'.o'); exe = self.output/label
            if self.run(label+'-codegen', [LLVM/'bin/llc', '-O0', '-filetype=obj',
                    '-relocation-model=pic', ir, '-o', obj]).returncode: raise RuntimeError('codegen')
            if self.run(label+'-link', ['/usr/bin/clang', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    PROJECT/'driver.c', obj, '-o', exe]).returncode: raise RuntimeError('link')
            result = self.run(label+'-execute', [exe])
            lines = result.stdout.splitlines()
            self.check(label+'-observation-count', len(lines) == 15)
            for line in lines:
                name, actual, expected = line.split('\t')
                self.check(label+'-'+name, int(actual) == int(expected))
            outputs[label] = result.stdout
        self.check('before-after-all-observations', outputs['before'] == outputs['after'])
        return outputs
