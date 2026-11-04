#!/usr/bin/env python3
"""Verify affine contracts and legal/illegal structured reorderings."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/14-structured-optimization'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,OPT,INSPECT,BUFFER,log_directory

def main():
    out=log_directory();e=Experiment(out);e.build()
    e.check('version','20.1.8' in e.run('version',[OPT,'--version']).stdout)
    root=WORKSPACE/'blog/docs/notes/compile/mlir'
    docs=[*(root/'dialects/affine').glob('*.md'),*(root/'compiler/optimization'/n for n in ['tiling.md','fusion.md','interchange.md'])]
    examples,shown={},{}
    for p in docs:
        for kind,name,code in re.findall(r'<!-- structured-(example|output): ([\w-]+) -->\s*```text\n(.*?)\n```',p.read_text(),re.S):
            (examples if kind=='example' else shown)[name]=code.strip()
    e.check('example-coverage',set(examples)=={'crop','triangle','affine-add','wave','elementwise'})
    for name,code in examples.items():e.check('shown-'+name,(PROJECT/(name+'.mlir')).read_text().strip()==code)
    for p in PROJECT.glob('*.mlir'):
        normal=e.artifact('parse-'+p.stem,[OPT,p]);generic=e.artifact('generic-'+p.stem,[OPT,p,'--mlir-print-op-generic'])
        again=e.artifact('reparse-'+p.stem,[OPT,generic]);e.check('roundtrip-'+p.stem,normal.read_text()==again.read_text())
    stages={name:e.stage(name) for name in ['base','affine-tile','fused','tiled','swapped']}
    affine=stages['affine-tile'].read_text()
    e.check('affine-tiling-four-loops',affine.count('affine.for')==4)
    e.check('affine-tiling-tail',affine.count('to min')==2 and 'd0 + 2, 5' in affine and 'd0 + 3, 7' in affine)
    e.check('elementwise-fused',stages['base'].read_text().count('linalg.generic')==2
        and stages['fused'].read_text().count('linalg.generic')==1)
    tiled=stages['tiled'].read_text()
    e.check('tensor-tile-structure',tiled.count('scf.for')==2 and tiled.count('tensor.extract_slice')==2
        and tiled.count('tensor.insert_slice')==1 and tiled.count('affine.min')==2)
    e.check('interchange-updates-map','affine_map<(d0, d1) -> (d1, d0)>' in stages['swapped'].read_text())
    for name,expected in [('base',2),('fused',1)]:
        buffer=e.artifact(name+'-buffer',[OPT,stages[name],*BUFFER,'--verify-each']).read_text()
        e.check(name+'-allocations',buffer.count('memref.alloc(')==expected)
    facts={}
    for name in ['affine-add','wave']:
        facts[name]=e.run(name+'-analysis',[INSPECT,PROJECT/(name+'.mlir')]).stdout
    e.check('wave-dependences',facts['wave'].splitlines()==['identity legal: 1','swap legal: 0','outer parallel: 0','inner parallel: 1'])
    e.check('independent-loop-dependences',facts['affine-add'].splitlines()==['identity legal: 1','swap legal: 1','outer parallel: 1','inner parallel: 1'])
    e.check('shown-query',shown.get('wave-analysis')==facts['wave'].strip())
    # affine.apply verifies arity/results, but not this full identifier rule.
    # affine.if is a consumer that checks symbol validity in the enclosing scope.
    bad=out/'invalid-symbol.mlir';bad.write_text((PROJECT/'triangle.mlir').read_text().replace(
        'affine.if #lower(%i, %j)', 'affine.if affine_set<()[s] : (s >= 0)>()[%i]'))
    r=e.run('reject-iv-as-symbol',[OPT,bad],expected=1)
    e.check('symbol-diagnostic','symbol' in r.stderr and 'cannot' in r.stderr)
    bad_map=out/'invalid-product.mlir';bad_map.write_text((PROJECT/'crop.mlir').read_text().replace(
        'affine_map<(i)[r0] -> (i + r0)>(%i)[%row0]',
        'affine_map<(i,j) -> (i * j)>(%i,%j)'))
    r=e.run('reject-dimension-product',[OPT,bad_map],expected=1)
    e.check('nonaffine-diagnostic','non-affine' in r.stderr or 'symbolic' in r.stderr)
    bad_schedule=out/'invalid-interchange.mlir';bad_schedule.write_text((PROJECT/'interchange.mlir').read_text().replace('[1, 0]','[0, 0]'))
    r=e.run('reject-non-permutation',[OPT,bad_schedule],expected=1)
    e.check('permutation-diagnostic','permutation' in r.stderr)
    rows=e.native();samples={r[1]:r[2:] for r in rows if r[0]=='sample'}
    e.check('crop-corners',samples.get('crop-corners')==['102','305'])
    e.check('wrong-interchange-concrete',samples.get('wave-at-2-0')==['4','102'])
    e.run('observe-entry',[sys.executable,PROJECT/'observe.py','--stage','dependence'])
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'scope':'5 algorithm fixtures + 2 schedules; real Affine tiling, elementwise fusion, Transform tiling/interchange; exact dependence query; invalid symbol/product/permutation; 33 native case checks including all coordinates, tails, empty shapes and wrong-but-defined interchange counterexample. No timing.',
        'files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed; 33 native case checks')
    print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))

if __name__=='__main__':main()
