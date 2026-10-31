#!/usr/bin/env python3
"""Validate memory chapter examples, decisions, lifetime IR and native results."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

WORKSPACE = Path(__file__).resolve().parents[3]
PROJECT = WORKSPACE / 'aicompiler-labs/llvm-mlir/10-memory-bufferization'
sys.path.insert(0, str(PROJECT))
from experiment import Commands, OPT, BUFFER_FLAGS, stage_flags, log_directory


def main():
    root = WORKSPACE / 'blog/docs/notes/compile/mlir'
    docs = [*(root / 'dialects/memref').glob('*.md'), *(root / 'compiler/memory').glob('*.md')]
    out = log_directory()
    c = Commands(out)
    version = c.run('version', [OPT, '--version'])
    c.check('llvm-version', '20.1.8' in version.stdout)
    examples, shown = {}, {}
    for path in docs:
        content = path.read_text()
        for kind, name, code in re.findall(r'<!-- memory-(example|output): ([\w-]+) -->\s*```text\n(.*?)\n```', content, re.S):
            destination = examples if kind == 'example' else shown
            if name in destination:
                c.check('same-example-' + name, destination[name] == code)
            destination[name] = code
    c.check('example-coverage', set(examples) == {p.stem for p in PROJECT.glob('*.mlir')})
    for name, code in examples.items():
        c.check('fixture-' + name, (PROJECT / (name + '.mlir')).read_text().strip() == code.strip())
        path = out / (name + '.mlir'); path.write_text(code + '\n')
        normal = c.artifact('parse-' + name, [OPT, path])
        generic = c.artifact('generic-' + name, [OPT, path, '--mlir-print-op-generic'])
        reparse = c.artifact('reparse-' + name, [OPT, generic])
        c.check('roundtrip-' + name, normal.read_text() == reparse.read_text())
    expected_shown = {'reuse-buffer', 'preserve-buffer', 'fill-preserve-buffer', 'tile-update-buffer',
                      'preserve-dealloc', 'call-dealloc', 'return-alias-dealloc', 'signature-buffer', 'branch-dealloc'}
    c.check('output-coverage', set(shown) == expected_shown)
    outputs = {}
    for tag, code in shown.items():
        name, stage = tag.rsplit('-', 1)
        path = c.artifact(tag, [OPT, PROJECT / (name + '.mlir'), *stage_flags(name, stage), '--verify-each'])
        outputs[tag] = path.read_text()
        c.check('printed-output-' + tag, code.strip() == path.read_text().strip())
    c.check('reuse-no-copy', 'memref.alloc' not in outputs['reuse-buffer']
            and 'memref.copy' not in outputs['reuse-buffer'] and 'memref.store' in outputs['reuse-buffer'])
    c.check('preserve-copy-before-store', outputs['preserve-buffer'].index('memref.copy') < outputs['preserve-buffer'].index('memref.store'))
    c.check('full-overwrite-no-initial-copy', 'memref.alloc' in outputs['fill-preserve-buffer']
            and 'memref.copy' not in outputs['fill-preserve-buffer'] and 'linalg.fill' in outputs['fill-preserve-buffer'])
    c.check('tile-reuses-view', outputs['tile-update-buffer'].count('memref.subview') == 1
            and 'memref.copy' not in outputs['tile-update-buffer'] and 'memref.alloc' not in outputs['tile-update-buffer'])
    c.check('local-lifetime', outputs['preserve-dealloc'].rindex('memref.load') < outputs['preserve-dealloc'].index('memref.dealloc')
            < outputs['preserve-dealloc'].index('return '))
    make, consume = outputs['call-dealloc'].split('func.func @consume')
    c.check('returned-allocation-retained', 'memref.dealloc' not in make and 'memref.dealloc' in consume)
    c.check('ownership-clone', 'bufferization.clone' in outputs['return-alias-dealloc'])
    c.check('branch-conditional-release', re.search(r'scf.if %arg1 \{\s+memref.dealloc', outputs['branch-dealloc']) is not None)
    for name, flag, diagnostic in [('reuse', 'true', None), ('preserve', 'false', 'CONFL-WRITE'), ('readonly', 'false', 'NOT-WRITABLE')]:
        path = c.artifact('analysis-' + name, [OPT, PROJECT / (name + '.mlir'), *stage_flags(name, 'analysis')])
        text = path.read_text()
        c.check('analysis-decision-' + name, f'["none", "{flag}", "none"]' in text)
        if diagnostic: c.check('analysis-reason-' + name, diagnostic in text)
    for name in ('branch', 'call'):
        path = c.artifact('ownership-' + name, [OPT, PROJECT / (name + '.mlir'), '--ownership-based-buffer-deallocation', '--verify-each'])
        c.check('ownership-intermediate-' + name, 'bufferization.dealloc' in path.read_text() and ('i1)' if name == 'branch' else 'retain') in path.read_text())
    # Parse succeeds without restrict, but One-Shot cannot analyze that boundary.
    no_restrict = out / 'no-restrict.mlir'
    no_restrict.write_text(examples['reuse'].replace('restrict writable', 'writable'))
    c.run('parse-no-restrict', [OPT, no_restrict])
    failure = c.run('buffer-no-restrict', [OPT, no_restrict, *BUFFER_FLAGS], expected=1)
    c.check('restrict-diagnostic', 'restrict' in failure.stderr)
    # The declared result layout must agree with the layout inferred by subview.
    bad_view = out / 'bad-view.mlir'
    bad_view.write_text(examples['view'].replace('strided<[4, 1], offset: 5>', 'strided<[2, 1], offset: 5>'))
    failure = c.run('wrong-view-layout', [OPT, bad_view], expected=1)
    c.check('view-diagnostic', 'stride' in failure.stderr.lower())
    # An unregistered op is only a diagnostic stand-in; it has no execution semantics.
    unknown = out / 'unknown.mlir'
    unknown.write_text(examples['reuse'].replace('%u = tensor.insert %v into %t[%c0] : tensor<4xi32>',
        '%u = "my.opaque"(%t) : (tensor<4xi32>) -> tensor<4xi32>'))
    c.run('parse-unknown', [OPT, unknown, '--allow-unregistered-dialect'])
    failure = c.run('reject-unknown', [OPT, unknown, '--allow-unregistered-dialect', *BUFFER_FLAGS], expected=1)
    c.check('unknown-diagnostic', 'bufferiz' in failure.stderr.lower())
    mixed = c.artifact('allow-unknown', [OPT, unknown, '--allow-unregistered-dialect', BUFFER_FLAGS[0] + ' allow-unknown-ops'])
    c.check('unknown-remains-mixed', 'my.opaque' in mixed.read_text() and 'bufferization.to_memref' in mixed.read_text())
    observations = c.numeric()
    c.check('numeric-count', len(observations) == 28)
    c.run('observation-entry', [sys.executable, PROJECT / 'observe.py', '--example', 'view'])
    files = [*docs, Path(__file__).resolve(), *(p for p in PROJECT.glob('*') if p.is_file())]
    manifest = {'date': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'llvm_commit': '87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'scope': 'parse/roundtrip, shown IR, analysis decisions, failure boundaries, ownership structure and 28 native scalar observations; concrete clone lowering checked without post-clone mutation; not a memory-safety proof or performance measurement',
        'files_sha256': {str(p.relative_to(WORKSPACE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'checks': c.checks}
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    failed = [item['name'] for item in c.checks if not item['passed']]
    print(f'{len(c.checks)-len(failed)}/{len(c.checks)} checks passed; {len(observations)} native scalar observations')
    print(out / 'manifest.json')
    if failed: raise SystemExit('Failed: ' + ', '.join(failed))


if __name__ == '__main__':
    main()
