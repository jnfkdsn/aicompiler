#!/usr/bin/env python3
"""Check Matmul tiling/unrolling and materialized/online Attention numerics."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/17-matmul-attention'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,OPT,log_directory

def main():
    out=log_directory();e=Experiment(out)
    e.check('version','20.1.8' in e.run('version',[OPT,'--version']).stdout)
    for p in PROJECT.glob('*.mlir'):
        normal=e.artifact('parse-'+p.stem,[OPT,p]);generic=e.artifact('generic-'+p.stem,[OPT,p,'--mlir-print-op-generic'])
        again=e.artifact('reparse-'+p.stem,[OPT,generic])
        e.check('roundtrip-'+p.stem,normal.read_text()==again.read_text())
    rows=e.native()
    tiled=(out/'tile-scheduled.mlir').read_text()
    e.check('tile-dimensions',tiled.count('scf.for')==3 and tiled.count('affine.min')==3)
    e.check('tile-views',tiled.count('memref.subview')==3 and 'memref.alloc' not in tiled)
    e.check('initialize-once',tiled.count('linalg.fill')==1 and tiled.index('linalg.fill')<tiled.index('scf.for'))
    unrolled=(out/'unroll-scheduled.mlir').read_text()
    e.check('unroll-main-and-remainder',unrolled.count('linalg.matmul')==3 and 'arith.constant 8 : index' in unrolled)
    values={r[1]:float(r[2]) for r in rows if r[0]=='value'}
    e.check('shown-result',values=={'materialized':28.0,'online':28.0})
    e.check('matmul-case-count',sum(r[0]=='matmul' for r in rows)==24)
    e.check('attention-case-count',sum(r[0]=='attention' for r in rows)==24)
    for name in ['attention','online']:
        text=(PROJECT/(name+'.mlir')).read_text()
        e.check('balanced-scratch-'+name,text.count('memref.alloc')==1 and text.count('memref.dealloc')==1)
    e.check('online-bounded-scratch','%scores = memref.alloc() : memref<3xf32>' in (PROJECT/'online.mlir').read_text())
    # Alter a state recurrence, retaining all memory bounds and loop structure.
    negout=out/'wrong-rescale';negout.mkdir();neg=Experiment(negout)
    wrong=neg.native(bad_online=True)
    e.checks.extend({'name':'negative-'+c['name'],**{k:v for k,v in c.items() if k!='name'}} for c in neg.checks)
    badvalues={r[1]:float(r[2]) for r in wrong if r[0]=='value'}
    e.check('shown-counterexample',badvalues=={'materialized':28.0,'online':40.0})
    failures=[r for r in wrong if r[0]!='value' and r[-1]!='1']
    e.check('negative-only-online',bool(failures) and all(r[0:2]==['attention','online'] for r in failures))
    root=WORKSPACE/'blog/docs/notes/compile/mlir/tutorials/kernels'
    docs=[root/(n+'.md') for n in ['matmul','attention','online_attention']]
    # The concrete core recurrence in the prose is taken from the executed IR.
    online=docs[2].read_text();fixture=(PROJECT/'online.mlir').read_text()
    core=next(c for c in re.findall(r'```text\n(.*?)\n```',online,re.S) if c.startswith('%delta ='))
    for line in core.splitlines():
        if line.strip() and not line.strip().startswith('//'):e.check('shown-recurrence-'+line.split('=')[0].strip(),line.strip() in fixture)
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'scope':'Three Matmul versions on 8 shapes, two Attention versions on 12 input families, CPU objects and double references; finite prefix masks and finite scores; safe incorrect online numerator rescaling. No device execution, throughput claim, arbitrary masks or nonfinite-input semantics.',
        'files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed; 48 native cases plus safe negative')
    print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))

if __name__=='__main__':main()
