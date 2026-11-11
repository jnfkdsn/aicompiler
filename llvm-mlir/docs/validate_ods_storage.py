#!/usr/bin/env python3
"""Validate grouping contracts, stored parameters and protocol consumers."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/20-ods-storage'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,BUILD,LLVM,log_directory

def main():
    out=log_directory();e=Experiment(out);e.build()
    e.check('version','20.1.8' in e.run('version',[LLVM/'bin/mlir-opt','--version']).stdout)
    normal=e.run('parse',[BUILD/'my-opt',PROJECT/'input.mlir']).stdout
    generic=e.run('generic',[BUILD/'my-opt',PROJECT/'input.mlir','--mlir-print-op-generic']).stdout
    p=out/'generic.mlir';p.write_text(generic)
    again=e.run('roundtrip',[BUILD/'my-opt',p]).stdout;e.check('same-roundtrip',again==normal)
    e.observe()
    # Each rejection targets a different invariant, never invalid memory access.
    cases=[
      ('segment-total','func.func @f(%x:i32)->i32 { %r="my.weighted_sum"(%x) <{operandSegmentSizes=array<i32: 1,1,0>}>:(i32)->i32 return %r:i32 }','operand count'),
      ('unequal','func.func @f(%x:i32)->i32 { %r=my.weighted_sum inputs(%x) weights() return %r:i32 }','equal input and weight counts'),
      ('seed-two','func.func @f(%x:i32)->i32 { %r="my.weighted_sum"(%x,%x) <{operandSegmentSizes=array<i32: 0,0,2>}>:(i32,i32)->i32 return %r:i32 }','requires 0 or 1 element'),
      ('group-total','func.func @f(%x:i32)->i32 { %r="my.group_sum"(%x) <{groupSizes=array<i32: 2>}>:(i32)->i32 return %r:i32 }','does not match with the total size'),
      ('group-results','func.func @f(%x:i32)->i32 { %r="my.group_sum"(%x) <{groupSizes=array<i32: 1,0>}>:(i32)->i32 return %r:i32 }','one result per group'),
      ('group-negative','func.func @f(%x:i32)->i32 { %r="my.group_sum"(%x) <{groupSizes=array<i32: -1,2>}>:(i32)->i32 return %r:i32 }','cannot have negative elements'),
      ('shape-zero','func.func private @f(!my.tile<[0,3]>)','positive dimensions'),
      ('shape-overflow','func.func private @f(!my.tile<[9223372036854775807,3]>)','representable byte count'),
      ('alignment','func.func private @f() attributes {my.policy=#my.alignment<3>}','power-of-two alignment')]
    for name,src,needle in cases:
        p=out/(name+'.mlir');p.write_text('module { '+src+' }\n')
        r=e.run('reject-'+name,[BUILD/'my-opt',p],1);e.check('diagnostic-'+name,needle in r.stderr)
    source=(PROJECT/'input.mlir').read_text()
    p=out/'no-note.mlir';p.write_text(source.replace(' {my.note = "example"}',''))
    a=e.run('original-lowered',[BUILD/'my-opt',PROJECT/'input.mlir','--my-lower-sums','--canonicalize']).stdout
    b=e.run('no-note-lowered',[BUILD/'my-opt',p,'--my-lower-sums','--canonicalize']).stdout
    e.check('discardable-does-not-change-compute',a==b)
    p=out/'no-seed.mlir';p.write_text(source.replace(' seed %c9',''))
    r=e.run('no-seed',[BUILD/'my-opt',p,'--my-inspect-segments','--my-lower-sums','--canonicalize'])
    e.check('optional-absent','weighted groups=2,2,0' in r.stderr and 'arith.constant 23 : i32' in r.stdout)
    docs=[WORKSPACE/'blog/docs/notes/compile/mlir/compiler/ir_definition'/(n+'.md') for n in ['complex_ods','storage_interfaces']]
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261','scope':'Actual ODS group queries/mutation, arith expansion and compile-time constants; owned storage/uniquing and Type/Attr protocol planning with bounds; programmatic recursive storage. No native kernel execution or Node serialization/lowering.', 'files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed');print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))
if __name__=='__main__':main()
