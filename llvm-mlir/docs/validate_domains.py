#!/usr/bin/env python3
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/25-domain-extensions'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,LLVM,log_directory

def main():
    out=log_directory();e=Experiment(out);e.observe()
    e.check('version','20.1.8' in e.run('version',[LLVM/'bin/mlir-opt','--version']).stdout)
    for p in PROJECT.glob('*.mlir'):
        flags=['--irdl-file='+str(PROJECT/'my.irdl.mlir')] if p.name=='dynamic.mlir' else []
        normal=e.ir('parse-'+p.stem,p,flags)
        e.ir('generic-'+p.stem,p,[*flags,'--mlir-print-op-generic'])
        again=e.ir('again-'+p.stem,out/('generic-'+p.stem+'.mlir'),flags)
        e.check('roundtrip-'+p.stem,normal.stdout==again.stdout)
    for name,src,flags,needle in [
        ('quant-storage',(PROJECT/'quant.mlir').read_text().replace('tensor<4xi8>','tensor<4xi16>'),[],'storage type in quantized type'),
        ('dynamic-type',(PROJECT/'dynamic.mlir').read_text().replace('i32','f32'),['--irdl-file='+str(PROJECT/'my.irdl.mlir')],"expected 'i32' but got 'f32'"),
        ('sparse-rank',(PROJECT/'sparse.mlir').read_text().replace('tensor<2x3xf32,#csr>','tensor<2x3x1xf32,#csr>'),[],'dimension-rank mismatch')]:
        p=out/(name+'.mlir');p.write_text(src);r=e.ir(name,p,flags,1);e.check(name+'-diagnostic',needle in r.stderr)
    p=out/'incompatible-shape.mlir';p.write_text((PROJECT/'shape.mlir').read_text().replace('[2,1]','[2,2]'))
    r=e.ir('incompatible-not-proven',p,['--canonicalize'])
    before=r.stdout.split('func.func @dynamic')[0]
    e.check('not-true-witness','shape.const_witness true' not in before and 'shape.cstr_broadcastable' in before)
    r=e.ir('dynamic-unregistered',PROJECT/'dynamic.mlir',[],1);e.check('registration-required','not found' in r.stderr or 'unregistered' in r.stderr)
    docs=[*(WORKSPACE/'blog/docs/notes/compile/mlir/dialects/extensions').glob('*.md'),WORKSPACE/'blog/docs/notes/compile/mlir/dialects/math/complex.md']
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261','scope':'Domain orientation: parsed/generic roundtrips; Quant boundary; sparse map preparation and loops; shape facts/constraints; IRDL dynamic validation and retained effects; complex arithmetic folds; TOSA->Linalg. Python numeric models separate. No domain runtime, target execution or StableHLO build.','files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed');print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))
if __name__=='__main__':main()
