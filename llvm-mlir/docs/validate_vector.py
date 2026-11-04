#!/usr/bin/env python3
"""Check Vector examples, Transform protocol, native values and timing records."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/15-vector-transform'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,OPT,LLVM,CODEGEN,log_directory,schedule

def main():
    out=log_directory();e=Experiment(out)
    e.check('version','20.1.8' in e.run('version',[OPT,'--version']).stdout)
    root=WORKSPACE/'blog/docs/notes/compile/mlir'
    docs=[*(root/'dialects/vector').glob('*.md'),*(root/'compiler/optimization'/n for n in ['vectorization.md','transform.md','performance.md'])]
    examples={}
    for p in docs:
        for name,code in re.findall(r'<!-- vector-example: ([\w-]+) -->\s*```text\n(.*?)\n```',p.read_text(),re.S):examples[name]=code.strip()
    e.check('example-coverage',set(examples)=={'elementwise','vectorize'})
    for name,code in examples.items():e.check('shown-'+name,(PROJECT/(name+'.mlir')).read_text().strip()==code)
    for p in PROJECT.glob('*.mlir'):
        normal=e.artifact('parse-'+p.stem,[OPT,p]);generic=e.artifact('generic-'+p.stem,[OPT,p,'--mlir-print-op-generic'])
        again=e.artifact('reparse-'+p.stem,[OPT,generic]);e.check('roundtrip-'+p.stem,normal.read_text()==again.read_text())
    values=(root/'dialects/vector/values.md').read_text()
    code=next(c for c in re.findall(r'```text\n(.*?)\n```',values,re.S) if c.startswith('func.func @values'))
    shown=out/'shown-values.mlir';shown.write_text(code+'\n');e.run('shown-values-parse',[OPT,shown])
    auto=e.automatic().read_text()
    e.check('auto-vectorizes',auto.count('scf.for')==1 and 'linalg.generic' not in auto and 'vector<4xf32>' in auto)
    e.check('auto-tail-structure',auto.count('vector.mask ')==2 and auto.count('memref.subview')==2 and 'affine.min' in auto)
    e.check('unused-output-read-removed',auto.count('vector.transfer_read')==1)
    source=PROJECT/'elementwise.mlir'
    r=e.run('suppress',[OPT,source,*schedule('suppress')]);e.check('suppression-retains-tile','scf.for' in r.stdout and 'linalg.generic' in r.stdout)
    e.check('suppression-continues','after suppressed failure' in r.stdout+r.stderr)
    propagate=out/'propagate.mlir';propagate.write_text((PROJECT/'suppress.mlir').read_text().replace('failures(suppress)','failures(propagate)'))
    r=e.run('propagate',[OPT,source,'--transform-preload-library=transform-library-paths='+str(propagate),'--transform-interpreter'],expected=1)
    e.check('propagate-diagnostic','cannot vectorize' in r.stderr)
    stale=out/'stale.mlir';stale.write_text((PROJECT/'vectorize.mlir').read_text().replace('vectorize %tiled','vectorize %target'))
    r=e.run('stale',[OPT,source,'--transform-preload-library=transform-library-paths='+str(stale),'--transform-interpreter'],expected=1)
    e.check('stale-diagnostic','handle invalidated' in r.stderr)
    bad=out/'bad-transpose.mlir';bad.write_text((PROJECT/'values.mlir').read_text().replace('[1, 0]','[0, 0]'))
    r=e.run('bad-transpose',[OPT,bad],expected=1);e.check('transpose-diagnostic','permutation' in r.stderr or 'more than once' in r.stderr)
    e.native()
    lowered=(out/'values-llvm.mlir').read_text()
    e.check('multidimensional-representation','!llvm.array<2 x vector<4xf32>>' in lowered)
    reduction=(out/'reduction-llvm.mlir').read_text()
    e.check('ordered-reduction','llvm.intr.vector.reduce.fadd' in reduction and '#llvm.fastmath<none>' in reduction)
    e.check('contract-lowered','vector.contract' not in reduction and 'llvm.intr.fmuladd' in reduction)
    reassoc=e.artifact('reassoc',[OPT,PROJECT/'reduction.mlir','--convert-vector-to-llvm=reassociate-fp-reductions'])
    e.check('reassoc-is-explicit','#llvm.fastmath<reassoc>' in reassoc.read_text())
    # A wrong-but-memory-safe mask drops live lanes. No out-of-bounds negative run.
    wrong=out/'wrong-mask.mlir';wrong.write_text((PROJECT/'masked.mlir').read_text().replace(
        '%mask = vector.create_mask %left', '%c1 = arith.constant 1 : index\n      %mask = vector.create_mask %c1'))
    lowered=e.lower('wrong-mask',wrong)
    ll=e.artifact('wrong-mask-translate',[LLVM/'bin/mlir-translate',lowered,'--mlir-to-llvmir'],'.ll')
    obj=out/'wrong-mask.o';e.run('wrong-mask-codegen',[LLVM/'bin/llc',*CODEGEN,'-filetype=obj',ll,'-o',obj])
    objects=[out/(n+'.o') for n in ['scalar','automatic','transfer','split','values','reduction']]
    exe=out/'wrong-driver';e.run('wrong-mask-link',['/usr/bin/clang','-O2',PROJECT/'driver.c',*objects,obj,'-lm','-o',exe])
    r=e.run('wrong-mask-execute',[exe],expected=1)
    failures=[l.split('\t')[1] for l in r.stdout.splitlines() if l.startswith('case\t') and l.split('\t')[3]!='0']
    e.check('wrong-mask-only-masked-fails',bool(failures) and all(n.startswith('masked-') for n in failures))
    e.check('scalar-asm','addss' in (out/'scalar.s').read_text())
    e.check('split-asm','movups' in (out/'split.s').read_text() and 'addps' in (out/'split.s').read_text())
    e.check('automatic-conditional-memory','testb' in (out/'automatic.s').read_text() and 'movss' in (out/'automatic.s').read_text())
    record=json.loads((PROJECT/'benchmark-record.json').read_text());obs=record['observations']
    e.check('reference-raw-samples',sum(row[0]=='raw' for row in obs)==81)
    e.check('reference-source-hash',record['benchmark_source_sha256']==hashlib.sha256((PROJECT/'benchmark.c').read_bytes()).hexdigest())
    for n,digest in record['kernel_source_sha256'].items():e.check('reference-kernel-'+n,hashlib.sha256((PROJECT/n).read_bytes()).hexdigest()==digest)
    measured={(row[1],int(row[2])):row for row in obs if row[0]=='bench'}
    performance=(root/'compiler/optimization/performance.md').read_text()
    for n in [1024,65536,4194304]:
        text='| '+str(n)+' | '+' | '.join(f'{float(measured[(v,n)][5])/1000:.3f}' for v in ['scalar','automatic','split'])+' |'
        e.check('shown-benchmark-'+str(n),text in performance)
    current=json.loads((out/'benchmark-observations.json').read_text())
    e.check('current-benchmark-observed',sum(row[0]=='bench' for row in current)==9 and sum(row[0]=='raw' for row in current)==81)
    # Timings are observations, never a speedup pass/fail threshold.
    for row in current:
        if row[0]=='bench':e.check('timing-valid-'+row[1]+row[2],0<float(row[4])<=float(row[5])<=float(row[6]))
    e.run('observe-entry',[sys.executable,PROJECT/'observe.py','--stage','automatic'])
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'scope':'Vector fixture roundtrips; automatic tile/vectorization; consume/failure protocol; 59 native cases; safe wrong-mask negative; default/reassoc lowering; x86-64 assembly; 81 current timing samples and frozen article reference. No speedup threshold or general floating-point equivalence claim.',
        'files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed; 59 native cases; 81 timing samples')
    print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))

if __name__=='__main__':main()
