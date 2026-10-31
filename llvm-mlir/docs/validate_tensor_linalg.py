#!/usr/bin/env python3
"""Validate self-contained Tensor/Linalg chapters and concrete compiled results."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

WORKSPACE = Path(__file__).resolve().parents[3]
PROJECT = WORKSPACE / 'aicompiler-labs/llvm-mlir/09-tensor-linalg'
sys.path.insert(0, str(PROJECT))
from experiment import Commands, OPT, LLVM, BUFFER_FLAGS, LOOP_FLAGS, log_directory


def main():
    root = WORKSPACE / 'blog/docs/notes/compile/mlir'
    docs = [root / 'tutorials/pipelines/overview.md',
            *(root / 'dialects/tensor').glob('*.md'),
            *(root / 'dialects/linalg').glob('*.md')]
    out = log_directory('tensor-linalg')
    c = Commands(out)
    version = c.run('mlir-version', [OPT, '--version'])
    c.check('pinned-major', '20.1.8' in version.stdout)
    examples, outputs = {}, {}
    for p in docs:
        content = p.read_text()
        for name, code in re.findall(r'<!-- tensor-example: ([\w-]+) -->\s*```text\n(.*?)\n```',content,re.S):
            if name in examples:
                c.check('same-example-' + name + '-' + p.stem, examples[name] == code)
            examples[name] = code
        for name, code in re.findall(r'<!-- tensor-output: ([\w-]+) -->\s*```text\n(.*?)\n```',content,re.S):
            outputs[name] = code
    c.check('examples-present', len(examples) == 17)
    c.check('outputs-present', set(outputs) == {'buffer-add','loops-add'})
    normalized = {}
    for name, code in examples.items():
        fixture = PROJECT / (name + '.mlir')
        c.check('fixture-' + name, fixture.is_file() and fixture.read_text().strip() == code.strip())
        p = out / (name + '.mlir')
        p.write_text(code + '\n')
        normal = c.artifact('parse-' + name, [OPT, p])
        normalized[name] = normal.read_text()
        generic = c.artifact('generic-' + name, [OPT, p, '--mlir-print-op-generic'])
        reparsed = c.artifact('reparse-' + name, [OPT, generic])
        c.check('roundtrip-' + name, reparsed.read_text() == normal.read_text())
    for stage, flags in [('buffer', BUFFER_FLAGS), ('loops', LOOP_FLAGS)]:
        path = c.artifact(stage + '-add', [OPT, PROJECT / 'add.mlir', *flags, '--verify-each'])
        c.check('shown-' + stage, path.read_text().strip() == outputs[stage+'-add'].strip())
    loop = (out / 'loops-add.mlir').read_text()
    c.check('loop-accesses', loop.count('scf.for ') == 2 and loop.count('memref.load ') == 2
            and loop.count('memref.store ') == 1 and 'arith.addf' in loop)
    general = c.artifact('generalize-matmul', [OPT, PROJECT / 'matmul.mlir', '--linalg-generalize-named-ops'])
    text = general.read_text()
    c.check('matmul-general-structure', 'linalg.matmul' not in text and 'arith.mulf' in text
            and 'arith.addf' in text and '["parallel", "parallel", "reduction"]' in text
            and '(d0, d1, d2) -> (d0, d2)' in text and '(d0, d1, d2) -> (d2, d1)' in text)
    folded = c.artifact('shape-canonicalize', [OPT, PROJECT / 'dynamic-shape.mlir', '--canonicalize'])
    c.check('static-dim-folded', 'arith.constant 3 : index' in folded.read_text()
            and folded.read_text().count('tensor.dim') == 1)
    invalid = [
        ('cast', examples['shape-cast'].replace('tensor<?x3xf32>', 'tensor<4x3xf32>'), 'are cast incompatible'),
        ('slice', examples['patch'].replace('[2, 2][1, 1]', '[3, 2][1, 1]',1), 'size mismatch'),
        ('collapse', examples['reshape'].replace('tensor<6xf32>', 'tensor<5xf32>'), 'to be static value of 6'),
        ('map', examples['add'].replace('iterator_types = ["parallel", "parallel"]','iterator_types = ["parallel"]'), 'to match the number of loops'),
        ('matmul', examples['matmul'].replace('tensor<3x2xf32>', 'tensor<4x2xf32>'), "to be 3, but found 4"),
    ]
    for name, code, diagnostic in invalid:
        p=out/('invalid-'+name+'.mlir'); p.write_text(code+'\n')
        result=c.run('invalid-'+name,[OPT,p],expected=1)
        c.check('diagnostic-'+name,diagnostic in result.stderr)
    observations = c.numeric()
    c.check('numeric-coverage', len(observations) == 109)
    c.run('observe-entry', [sys.executable, PROJECT / 'observe.py', '--example', 'patch'])
    files = [*docs, Path(__file__).resolve(), *(p for p in PROJECT.glob('*') if p.is_file())]
    manifest = {'date': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'llvm_commit': '87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'scope': 'parse/verify, roundtrip, transformations, diagnostics and 109 scalar observations from a native CPU executable; no performance or general floating-point-error claim',
        'files_sha256': {str(p.relative_to(WORKSPACE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'checks': c.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[item['name'] for item in c.checks if not item['passed']]
    print(f'{len(c.checks)-len(failed)}/{len(c.checks)} checks passed; {len(observations)} numeric observations')
    print(out/'manifest.json')
    if failed: raise SystemExit('Failed: '+', '.join(failed))


if __name__ == '__main__':
    main()
