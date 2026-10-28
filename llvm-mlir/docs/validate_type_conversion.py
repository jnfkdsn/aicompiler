#!/usr/bin/env python3
"""Check Conversion chapters against compiled LLVM 20.1.8 examples."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import textwrap


def main():
    workspace = Path(__file__).resolve().parents[3]
    project = workspace / 'aicompiler-labs/llvm-mlir/08-type-conversion'
    chapters = workspace / 'blog/docs/notes/compile/mlir/compiler/conversion'
    build = workspace / 'artifacts/builds/mlir-type-conversion'
    out = workspace / 'artifacts/logs/mlir-docs' / datetime.now().strftime('%Y-%m-%d-%H%M%S-type-conversion')
    out.mkdir(parents=True)
    checks = []

    def check(name, ok):
        checks.append({'name': name, 'passed': bool(ok)})

    def run(name, command, expected=0, timeout=30):
        command = [str(x) for x in command]
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        (out / (name + '.stdout.txt')).write_text(result.stdout)
        (out / (name + '.stderr.txt')).write_text(result.stderr)
        checks.append({'name': name, 'command': command, 'exit_code': result.returncode,
                       'expected_exit': expected, 'passed': result.returncode == expected})
        return result

    result = run('build', [sys.executable, project / 'observe.py', '--build-only'], timeout=300)
    if result.returncode:
        raise SystemExit(f'Build failed; see {out}')
    docs = [chapters / (name + '.md') for name in ['type_conversion', 'materialization', 'boundaries', 'advanced']]
    content = '\n'.join(p.read_text() for p in docs)
    source = (project / 'RangeConversion.cpp').read_text()
    regions = {n: textwrap.dedent(c).strip() for n, c in re.findall(
        r'// BEGIN: ([\w-]+)\n(.*?)\s*// END: \1', source, re.S)}
    snippets = re.findall(r'<!-- range-source: ([\w-]+) -->\s*```cpp\n(.*?)\n```', content, re.S)
    check('source-coverage', len(snippets) == 12)
    for name, code in snippets:
        check('source-' + name, regions.get(name) == code.strip())
    examples = dict(re.findall(r'<!-- range-example: ([\w-]+) -->\s*```text\n(.*?)\n```', content, re.S))
    outputs = dict(re.findall(r'<!-- range-output: ([\w-]+) -->\s*```text\n(.*?)\n```', content, re.S))
    check('example-coverage', set(examples) == {'limit', 'calls', 'scope', 'cast-roundtrip'})
    check('output-coverage', set(outputs) == {'limit', 'partial', 'finished', 'calls', 'scope'})
    opt, probe = build / 'range-opt', build / 'range-probe'
    pipeline = '--pass-pipeline=builtin.module(my-convert-range)'
    originals = {}
    for name, code in examples.items():
        path = out / (name + '.mlir')
        path.write_text(code + '\n')
        check('fixture-' + name, code.strip() == (project / path.name).read_text().strip())
        originals[name] = run('parse-' + name, [opt, path]).stdout
        generic = run('generic-' + name, [opt, path, '--mlir-print-op-generic'])
        gp = out / (name + '-generic.mlir')
        gp.write_text(generic.stdout)
        restored = run('roundtrip-' + name, [opt, gp])
        check('roundtrip-equal-' + name, restored.stdout == originals[name])
    actual = {}
    for name in ['limit', 'calls', 'scope', 'branch']:
        actual[name] = run('full-' + name, [probe, 'full', project / (name + '.mlir')]).stdout
        check('range-removed-' + name, '!my.range' not in actual[name] and 'my.limit' not in actual[name]
              and 'unrealized_conversion_cast' not in actual[name])
        if name in outputs:
            check('shown-output-' + name, actual[name].strip() == outputs[name].strip())
    passed = run('pass', [opt, project / 'limit.mlir', pipeline, '--verify-each'])
    check('pass-equals-probe', passed.stdout.strip() == actual['limit'].strip())
    no_bridge = run('full-no-bridge', [probe, 'full-no-bridge', project / 'limit.mlir'])
    check('full-needs-no-bridge', no_bridge.stdout == actual['limit'])
    partial = run('partial', [probe, 'partial', project / 'limit.mlir'])
    partial_path = out / 'partial.mlir'
    partial_path.write_text(partial.stdout)
    check('shown-output-partial', partial.stdout.strip() == outputs['partial'].strip())
    check('partial-live-cast', partial.stdout.count('unrealized_conversion_cast') == 1
          and '-> !my.range<-4, 7>' in partial.stdout)
    failed = run('partial-no-bridge', [probe, 'partial-no-bridge', project / 'limit.mlir'], 1)
    check('materialization-diagnostic', 'failed to legalize unresolved materialization' in failed.stderr
          and 'remained live after conversion' in failed.stderr)
    for mode in ['full', 'finish']:
        completed = run('partial-then-' + mode, [probe, mode, partial_path])
        check('shown-output-finished-' + mode, completed.stdout.strip() == outputs['finished'].strip()
              == actual['limit'].strip())
    kept = run('reconcile-live', [opt, partial_path, '--reconcile-unrealized-casts'])
    check('reconcile-keeps-live-boundary', kept.stdout.strip() == partial.stdout.strip())
    folded = run('reconcile-roundtrip', [opt, project / 'cast-roundtrip.mlir', '--reconcile-unrealized-casts'])
    check('reconcile-removes-roundtrip', 'unrealized_conversion_cast' not in folded.stdout
          and 'return %arg0 : i32' in folded.stdout)
    for mode, name, op in [('no-call', 'calls', 'func.call'), ('no-yield', 'scope', 'my.yield')]:
        result = run(mode, [probe, mode, project / (name + '.mlir')], 1)
        check(mode + '-diagnostic', f"failed to legalize operation '{op}'" in result.stderr)
    check('call-consumes-new-result', 'call @keep(%1) : (i32) -> i32' in actual['calls'])
    check('scope-entry-exit', '^bb0(%arg1: i32)' in actual['scope'] and 'my.yield %arg1 : i32' in actual['scope'])
    check('branch-argument', 'cf.br ^bb1(%1 : i32)' in actual['branch'] and '^bb1(%' in actual['branch'])
    # Region arity and nesting must survive parent reconstruction.
    extra = {
        'scope-zero': '''module { func.func @zero() {
          "my.scope"() ({ my.yield }) : () -> ()
          return
        }}''',
        'scope-multi': '''module { func.func @multi(%x: i32) -> (!my.range<-4, 7>, i32) {
          %a, %b = "my.scope"(%x) ({ ^bb0(%local: i32):
            %r = my.limit %local bounds(#my.bounds<-4, 7>) : !my.range<-4, 7>
            my.yield %r, %local : !my.range<-4, 7>, i32
          }) : (i32) -> (!my.range<-4, 7>, i32)
          return %a, %b : !my.range<-4, 7>, i32
        }}''',
        'scope-nested': '''module { func.func @nested(%x: !my.range<-4, 7>) -> !my.range<-4, 7> {
          %a = "my.scope"(%x) ({ ^bb0(%v: !my.range<-4, 7>):
            %b = "my.scope"(%v) ({ ^bb0(%w: !my.range<-4, 7>):
              my.yield %w : !my.range<-4, 7>
            }) : (!my.range<-4, 7>) -> !my.range<-4, 7>
            my.yield %b : !my.range<-4, 7>
          }) : (!my.range<-4, 7>) -> !my.range<-4, 7>
          return %a : !my.range<-4, 7>
        }}''',
    }
    for name, code in extra.items():
        p = out / (name + '.mlir')
        p.write_text(code + '\n')
        result = run(name, [opt, p, pipeline, '--verify-each'])
        check(name + '-types', '!my.range' not in result.stdout and 'my.limit' not in result.stdout
              and 'unrealized_conversion_cast' not in result.stdout)
        check(name + '-regions-retained', result.stdout.count('"my.scope"') == code.count('"my.scope"'))
    for name, bounds in [('equal', '7, 7'), ('extreme', '-2147483648, 2147483647')]:
        p = out / (name + '.mlir')
        p.write_text(examples['limit'].replace('-4, 7', bounds))
        result = run(name, [opt, p, pipeline, '--verify-each'])
        check(name + '-arith', '!my.range' not in result.stdout and 'arith.minsi' in result.stdout)
        for value in bounds.split(', '):
            check(name + '-constant-' + value, f'arith.constant {value} : i32' in result.stdout)
    invalid = out / 'invalid.mlir'
    invalid.write_text(examples['limit'].replace('#my.bounds<-4, 7>', '#my.bounds<-3, 7>'))
    invalid_result = run('invalid-before-conversion', [probe, 'full', invalid], 2)
    check('invalid-is-verifier-failure', 'error:' in invalid_result.stderr and 'failed to legalize' not in invalid_result.stderr)
    for name in ['limit', 'analysis-mixed']:
        normal = run('original-' + name, [opt, project / (name + '.mlir')])
        analyzed = run('analysis-' + name, [probe, 'analysis', project / (name + '.mlir')])
        check('analysis-preserves-' + name, analyzed.stdout.strip() == normal.stdout.strip())
        check('analysis-reports-' + name, 'limit_legalizable=1' in analyzed.stderr)
    result = run('full-mixed', [probe, 'full', project / 'analysis-mixed.mlir'], 1)
    check('analysis-not-full-guarantee', "failed to legalize operation 'my.clamp'" in result.stderr)
    result = run('recursive', [probe, 'recursive', project / 'limit.mlir'])
    check('recursive-skips-limit', result.stdout.strip() == originals['limit'].strip())
    unresolved = out / 'unresolved.mlir'
    unresolved.write_text('''module { func.func @unresolved(%x: i32) -> f32 {
      %r = builtin.unrealized_conversion_cast %x : i32 to f32
      return %r : f32
    }}''')
    run('full-allows-placeholder', [probe, 'full', unresolved])
    guarded = run('finish-rejects-placeholder', [probe, 'finish', unresolved], 1)
    check('final-guard-diagnostic', 'unresolved boundary remains' in guarded.stderr)
    run('observe', [sys.executable, project / 'observe.py'], timeout=300)
    files = [*docs, Path(__file__).resolve(), *sorted(p for p in project.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts)]
    manifest = {'date': datetime.now().isoformat(),
        'llvm_commit': '87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'scope': 'Compiler-side parse/verify/conversion/source-output consistency; no numeric execution',
        'files_sha256': {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'checks': checks}
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    failures = [c['name'] for c in checks if not c['passed']]
    print(f'{len(checks)-len(failures)}/{len(checks)} checks passed; {out / "manifest.json"}')
    if failures:
        raise SystemExit('Failed: ' + ', '.join(failures))


if __name__ == '__main__':
    main()
