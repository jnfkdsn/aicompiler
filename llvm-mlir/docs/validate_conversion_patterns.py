#!/usr/bin/env python3
"""Validate 1:N boundary closure/native values and both declarative rule paths."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/21-conversion-patterns'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,BUILD,LLVM,log_directory

def main():
    out=log_directory();e=Experiment(out);e.build()
    e.check('version','20.1.8' in e.run('version',[LLVM/'bin/mlir-opt','--version']).stdout)
    for p in PROJECT.glob('*.mlir'):
        plain=e.artifact('parse-'+p.stem,[BUILD/'my-opt',p])
        generic=e.artifact('generic-'+p.stem,[BUILD/'my-opt',p,'--mlir-print-op-generic'])
        again=e.artifact('again-'+p.stem,[BUILD/'my-opt',generic])
        e.check('roundtrip-'+p.stem,plain.read_text()==again.read_text())
    e.pairs();e.patterns()
    e.check('noncommutative-native','difference=-2 expected -2' in (out/'native.stdout.txt').read_text())
    for name,src,flag,needle in [
      ('unsupported-tuple','func.func private @bad(tuple<i32,i64>)','--my-flatten-pairs',"failed to legalize operation 'func.func'"),
      ('invalid-pack','func.func @bad(%x:i32)->tuple<i32> { %p=my.pack %x,%x:tuple<i32> return %p:tuple<i32> }',None,'requires a pair'),
      ('wrong-domain','func.func @bad(%a:f32,%b:f32)->f32 { %r="my.add"(%a,%b):(f32,f32)->f32 return %r:f32 }',None,'32-bit signless integer')]:
        p=out/(name+'.mlir');p.write_text('module { '+src+' }\n')
        cmd=[BUILD/'my-opt',p]+([flag] if flag else [])
        r=e.run('reject-'+name,cmd,1);e.check('diagnostic-'+name,needle in r.stderr)
    # A syntactically invalid rule is rejected before it can enter the driver.
    p=out/'bad.pdll';p.write_text((PROJECT/'patterns.pdll').read_text().replace('replace root with x','replace missing with x'))
    r=e.run('reject-pdll',[LLVM/'bin/mlir-pdll',p,'-I',PROJECT,'-I',WORKSPACE/'upstream/llvm-project/mlir/include','-x=mlir'],1)
    e.check('undefined-root','undefined reference to `missing`' in r.stderr)
    docs=[WORKSPACE/'blog/docs/notes/compile/mlir/compiler/conversion/one_to_many.md',WORKSPACE/'blog/docs/notes/compile/mlir/compiler/transforms/declarative_patterns.md']
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261','scope':'Tuple pair expands across function/call/return/unconditional CFG branch; four native inputs with sum and noncommutative difference; DRR and PDLL generate same right-zero rewrite with left/nonzero and canonicalize-only controls. No general tuple/SCF/ABI or floating point proof.', 'files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed');print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))
if __name__=='__main__':main()
