#!/usr/bin/env python3
"""Validate the conversion chapter's source, outputs and legality contracts."""
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
    project = workspace / 'aicompiler-labs/llvm-mlir/07-dialect-conversion'
    chapter = workspace / 'blog/docs/notes/compile/mlir/compiler/conversion/operation_conversion.md'
    build = workspace / 'artifacts/builds/mlir-dialect-conversion'
    out = workspace / 'artifacts/logs/mlir-docs' / datetime.now().strftime('%Y-%m-%d-%H%M%S-conversion')
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

    built = run('build', [sys.executable, project / 'observe.py', '--build-only'], timeout=300)
    if built.returncode:
        raise SystemExit(f'Build failed; see {out}')
    content = chapter.read_text()
    source = '\n'.join(p.read_text() for p in project.glob('*.cpp'))
    regions = {n: textwrap.dedent(c).strip() for n, c in re.findall(
        r'// BEGIN: ([\w-]+)\n(.*?)\s*// END: \1', source, re.S)}
    snippets = re.findall(r'<!-- conversion-source: ([\w-]+) -->\s*```cpp\n(.*?)\n```', content, re.S)
    check('core-source-present', {n for n, _ in snippets} == {'target', 'pattern', 'pass', 'dynamic-target'})
    for name, code in snippets:
        check('source-' + name, regions.get(name) == code.strip())
    examples = dict(re.findall(r'<!-- conversion-example: ([\w-]+) -->\s*```text\n(.*?)\n```', content, re.S))
    check('chapter-examples-present', set(examples) == {'input', 'expanded', 'mixed', 'wide'})
    opt, probe = build / 'my-convert-opt', build / 'conversion-probe'
    pipeline = '--pass-pipeline=builtin.module(my-clamp-to-arith)'
    for name, code in examples.items():
        path = out / (name + '.mlir')
        path.write_text(code + '\n')
        run('parse-' + name, [opt, path])
        if (project / path.name).exists():
            check('fixture-' + name, code.strip() == (project / path.name).read_text().strip())
    converted = run('pass', [opt, project / 'input.mlir', pipeline, '--verify-each'])
    expected_ir = run('normalize-expanded', [opt, out / 'expanded.mlir'])
    check('pass-complete-expected-ir', converted.stdout == expected_ir.stdout)
    shown = re.search(r'<!-- conversion-output: expanded -->\s*```text\n(.*?)\n```', content, re.S)
    check('actual-output-in-chapter', shown is not None and shown[1].strip() == converted.stdout.strip())
    normalized = out / 'converted.mlir'
    normalized.write_text(converted.stdout)
    second = run('second-conversion', [opt, normalized, pipeline, '--verify-each'])
    check('already-legal-unchanged', second.stdout == converted.stdout)
    # Same source and target: distinguish known illegal, unknown and dynamic false.
    cases = [
        ('full', 'input', 0, ''), ('partial', 'input', 0, ''),
        ('full-no-rule', 'input', 1, "failed to legalize operation 'my.clamp'"),
        ('partial-no-rule', 'input', 1, 'explicitly marked illegal'),
        ('full-no-constant', 'input', 1, "failed to legalize operation 'my.clamp'"),
        ('partial-no-constant', 'input', 1, 'explicitly marked illegal'),
        ('full', 'mixed', 1, "failed to legalize operation 'arith.addi'"),
        ('partial', 'mixed', 0, ''),
        ('full', 'wide', 0, ''), ('partial', 'wide', 0, ''),
        ('full-dynamic', 'wide', 1, "failed to legalize operation 'arith.maxsi'"),
        ('partial-dynamic', 'wide', 1, 'explicitly marked illegal'),
        ('full-dynamic', 'input', 0, ''), ('partial-dynamic', 'input', 0, ''),
    ]
    outputs = {}
    for mode, name, expected, diagnostic in cases:
        result = run(mode + '-' + name, [probe, mode, project / (name + '.mlir')], expected)
        outputs[mode, name] = result.stdout
        check(mode + '-' + name + '-phase', ('conversion=failed' if expected else 'conversion=success') in result.stderr)
        if diagnostic:
            check(mode + '-' + name + '-diagnostic', diagnostic in result.stderr)
    check('full-probe-equals-pass', outputs['full', 'input'].strip() == converted.stdout.strip())
    mixed = outputs['partial', 'mixed']
    check('partial-updates-unknown-user', 'my.clamp' not in mixed and bool(re.search(
        r'(%\w+) = arith.minsi [^\n]+\n\s+(%\w+) = arith.addi \1, (%\w+) : i32\n\s+return \2 : i32', mixed)))
    chain = run('chain', [opt, project / 'chain.mlir', pipeline, '--verify-each'])
    mins = re.findall(r'(%\w+) = arith.minsi ', chain.stdout)
    check('chain-count', 'my.clamp' not in chain.stdout and len(mins) == 2)
    if len(mins) == 2:
        check('chain-next-consumer', f'arith.maxsi {mins[0]}, %c-2_i32' in chain.stdout)
        check('chain-second-use', f'arith.maxsi {mins[0]}, {mins[1]}' in chain.stdout)
    # The same pattern must handle valid signed extremes and equal bounds.
    for name, bounds in [('equal', '7, 7'), ('extreme', '-2147483648, 2147483647')]:
        path = out / (name + '.mlir')
        path.write_text(examples['input'].replace('-4, 7', bounds) + '\n')
        result = run(name, [opt, path, pipeline, '--verify-each'])
        check(name + '-expanded', 'my.clamp' not in result.stdout and
              'arith.maxsi' in result.stdout and 'arith.minsi' in result.stdout)
        for value in bounds.split(', '):
            check(name + '-constant-' + value, f'arith.constant {value} : i32' in result.stdout)
    invalid = out / 'invalid-bounds.mlir'
    invalid.write_text(examples['input'].replace('-4, 7', '8, 7') + '\n')
    rejected = run('invalid-before-conversion', [probe, 'full', invalid], expected=2)
    check('verifier-distinct-from-conversion', 'requires lower <= upper' in rejected.stderr
          and 'conversion=failed' not in rejected.stderr)
    # Exercise the public observation entry as well as its underlying commands.
    run('observe', [sys.executable, project / 'observe.py'], timeout=300)
    files = [chapter, Path(__file__).resolve(), *sorted(p for p in project.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts)]
    manifest = {'date': datetime.now().isoformat(),
        'llvm_commit': '87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'files_sha256': {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'checks': checks}
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    failures = [c['name'] for c in checks if not c['passed']]
    print(f'{len(checks)-len(failures)}/{len(checks)} checks passed; {out / "manifest.json"}')
    if failures:
        raise SystemExit('Failed: ' + ', '.join(failures))


if __name__ == '__main__':
    main()
