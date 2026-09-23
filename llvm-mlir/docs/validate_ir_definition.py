#!/usr/bin/env python3
"""Validate the IR-definition chapters against compiled code and behavior."""
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
    project = workspace / 'aicompiler-labs/llvm-mlir/06-ir-definition'
    docs = workspace / 'blog/docs/notes/compile/mlir/compiler/ir_definition'
    pages = [docs / (n + '.md') for n in ('traits_interfaces', 'types_attributes', 'regions_assembly', 'assembly_format')]
    build = workspace / 'artifacts/builds/mlir-ir-definition'
    out = workspace / 'artifacts/logs/mlir-docs' / datetime.now().strftime('%Y-%m-%d-ir-definition')
    out.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})

    def run(name, command, expected=0, timeout=30):
        command = [str(x) for x in command]
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        (out / (name + '.stdout.txt')).write_text(result.stdout)
        (out / (name + '.stderr.txt')).write_text(result.stderr)
        checks.append({'name': name, 'command': command, 'exit_code': result.returncode,
                       'passed': result.returncode == expected})
        return result

    built = run('build-observe', [sys.executable, project / 'observe.py'], timeout=300)
    if built.returncode:
        raise SystemExit(f'Build/observation failed; see {out}')
    content = '\n'.join(p.read_text() for p in pages)
    sources = '\n'.join(p.read_text() for p in sorted(project.iterdir()) if p.suffix in ('.cpp', '.td'))
    regions = {name: textwrap.dedent(code).strip() for name, code in re.findall(
        r'// BEGIN: ([\w-]+)\n(.*?)\s*// END: \1', sources, re.S)}
    snippets = re.findall(r'<!-- source-example: ([\w-]+) -->\s*```(?:cpp|text)\n(.*?)\n```', content, re.S)
    check('all-source-regions', set(regions) == {n for n, _ in snippets} and len(snippets) == len(regions))
    for name, code in snippets:
        check('source-' + name, regions.get(name) == code.strip())
    matches = re.findall(r'<!-- irdef-(example|invalid): ([^\n]+?) -->\s*```text\n(.*?)\n```', content, re.S)
    check('expected-document-examples', len(matches) == 7)
    check('unique-ids', len({spec.split('|')[0].strip() for _, spec, _ in matches}) == len(matches))
    opt = build / 'lesson-opt'
    for kind, spec, code in matches:
        parts = spec.split('|', 1)
        name = parts[0].strip()
        path = out / (name + '.mlir')
        path.write_text(code + '\n')
        result = run(name, [opt, path], expected=1 if kind == 'invalid' else 0)
        if kind == 'invalid':
            check(name + '-diagnostic', len(parts) == 2 and parts[1].strip() in result.stderr)
        else:
            check(name + '-fixture', code.strip() == (project / (name.removesuffix('-input') + '.mlir')).read_text().strip())
            generic = run(name + '-generic', [opt, path, '--mlir-print-op-generic'])
            genpath = out / (name + '-generic.mlir')
            genpath.write_text(generic.stdout)
            again = run(name + '-roundtrip', [opt, genpath])
            check(name + '-roundtrip-equal', result.stdout == again.stdout)
    report = '--pass-pipeline=builtin.module(func.func(lesson-report))'
    yes = run('external-model', [opt, project / 'interfaces.mlir', report])
    no = run('no-external-model', [build / 'lesson-opt-no-model', project / 'interfaces.mlir', report])
    check('model-adds-only-bounds', yes.stderr == no.stderr.replace(
        'lab.clamp effect_interface=1 speculatable=1 dead=1 bounds=unknown',
        'lab.clamp effect_interface=1 speculatable=1 dead=1 bounds=[-4,7]')
        and 'bounds=unknown' in no.stderr)
    check('effect-and-dead-reports', yes.stderr.splitlines() == [
        'lab.clamp effect_interface=1 speculatable=1 dead=1 bounds=[-4,7]',
        'lesson.opaque_clamp effect_interface=0 speculatable=0 dead=0 bounds=unknown'])
    cleaned = run('dead-code', [opt, project / 'interfaces.mlir', '--canonicalize', '--verify-each'])
    check('unknown-effects-retained', 'lab.clamp' not in cleaned.stdout
          and cleaned.stdout.count('"lesson.opaque_clamp"') == 1
          and 'lower = -4 : i32, upper = 7 : i32' in cleaned.stdout)
    used = out / 'used.mlir'
    used.write_text('module {\n func.func @used(%x: i32) -> i32 {\n'
                    '  %r = lab.clamp %x bounds(-4, 7) : i32\n  return %r : i32\n }\n}\n')
    used_report = run('used-report', [opt, used, report])
    check('used-result-not-dead', 'dead=0 bounds=[-4,7]' in used_report.stderr)
    used_clean = run('used-cleanup', [opt, used, '--canonicalize', '--verify-each'])
    check('used-clamp-preserved', 'lab.clamp' in used_clean.stdout and bool(re.search(
        r'(%\w+) = lab.clamp .*?\n\s+return \1 : i32', used_clean.stdout)))
    direct_scalar = run('direct-scalar-model', [build / 'lesson-opt-no-model', project / 'direct.mlir', report])
    check('direct-scalar-answer', direct_scalar.stderr.strip() ==
          'lesson.clamp effect_interface=1 speculatable=1 dead=0 bounds=[-4,7]')
    direct_bad = out / 'direct-invalid.mlir'
    direct_bad.write_text((project / 'direct.mlir').read_text().replace('bounds(-4, 7)', 'bounds(8, 7)'))
    rejected_direct = run('direct-invalid', [opt, direct_bad], expected=1)
    check('direct-invalid-diagnostic', 'requires lower <= upper' in rejected_direct.stderr)
    direct = run('direct-model', [build / 'lesson-opt-no-model', project / 'types.mlir', report])
    check('direct-interface-independent', direct.stderr.strip() ==
          'lesson.limit effect_interface=1 speculatable=1 dead=0 bounds=[-4,7]')
    probe = run('type-probe', [build / 'type-probe'])
    check('uniquing-and-checked', probe.stdout == 'same_parameters=1 different_parameters=0\ninvalid_is_null=1\n'
          and 'expected ordered bounds within signed i32 range' in probe.stderr)
    full = out / 'full-i32-range.mlir'
    full.write_text((project / 'types.mlir').read_text().replace('-4, 7', '-2147483648, 2147483647'))
    run('inclusive-i32-boundaries', [opt, full])
    singleton = out / 'singleton.mlir'
    singleton.write_text((project / 'types.mlir').read_text().replace('-4, 7', '7, 7'))
    run('singleton-range', [opt, singleton])
    scope = run('scope-preserved', [opt, project / 'scope.mlir'])
    check('swap-bindings', bool(re.search(
        r'\^bb0\((%\w+): i32, (%\w+): i64\):\s+lesson.yield \2, \1 : i64, i32', scope.stdout)))
    check('zero-and-multiple-results', 'func.func @empty()' in scope.stdout
          and ': (i32, i64) -> (i64, i32)' in scope.stdout and '}) : () -> ()' in scope.stdout)
    identity = run('identity-generic', [opt, project / 'assembly.mlir', '--mlir-print-op-generic'])
    check('identity-preserves-reference-and-attr', bool(re.search(
        r'\^bb0\((%\w+): i32\):\s+(%\w+) = "lesson.identity"\(\1\) \{tag = "demo"\} : \(i32\) -> i32\s+"func.return"\(\2\)', identity.stdout)))
    run('invalid-diagnostics', [opt, project / 'tests/invalid.mlir', '--split-input-file', '--verify-diagnostics', '-o', '/dev/null'])
    check('negative-coverage', (project / 'tests/invalid.mlir').read_text().count('expected-error') == 15)
    # Check the generated-code facts described in the type/storage chapter.
    storage = (build / 'LessonTypes.cpp.inc').read_text()
    check('generated-storage-key', 'KeyTy = std::tuple<int64_t, int64_t>' in storage and 'RangeType::getChecked' in storage)
    header = (build / 'LessonOps.h.inc').read_text()
    check('inherent-bounds-property', 'using boundsTy = ::mlir::lesson::BoundsAttr;' in header)
    version = run('version', [opt, '--version']).stdout
    files = [*pages, Path(__file__).resolve(), *sorted(p for p in project.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts), *sorted(build.glob('*.inc'))]
    manifest = {'date': datetime.now().isoformat(), 'version': version,
        'llvm_commit': '87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'files_sha256': {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'checks': checks}
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    failures = [c['name'] for c in checks if not c['passed']]
    print(f'{len(checks) - len(failures)}/{len(checks)} checks passed; {out / "manifest.json"}')
    if failures:
        raise SystemExit('Failed: ' + ', '.join(failures))


if __name__ == '__main__':
    main()
