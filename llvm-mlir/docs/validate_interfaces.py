#!/usr/bin/env python3
"""Build and check bufferization, type/shape and control-flow consumers."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/19-extension-interfaces'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,BUILD,OPT,log_directory

def main():
    out=log_directory();e=Experiment(out);e.build()
    e.check('version','20.1.8' in e.run('version',[OPT,'--version']).stdout)
    for p in PROJECT.glob('*.mlir'):
        normal=e.artifact('parse-'+p.stem,[BUILD/'my-opt',p])
        generic=e.artifact('generic-'+p.stem,[BUILD/'my-opt',p,'--mlir-print-op-generic'])
        again=e.artifact('roundtrip-'+p.stem,[BUILD/'my-opt',generic])
        e.check('same-'+p.stem,normal.read_text()==again.read_text())
    e.buffer();e.shape();e.control()
    for name,src,needle in [
        ('rank','module {func.func @bad(%a:tensor<2x2xf32>)->tensor<2x2xf32> { %r=my.add_one %a outs(%a):tensor<2x2xf32> return %r:tensor<2x2xf32> }}','requires a rank-one'),
        ('types','module {func.func @bad(%a:tensor<4xf32>,%b:tensor<5xf32>)->tensor<4xf32> { %r="my.add_one"(%a,%b):(tensor<4xf32>,tensor<5xf32>)->tensor<4xf32> return %r:tensor<4xf32> }}','same type'),
        ('empty-scope','module {func.func @bad(%a:i32)->i32 { %r="my.scope"(%a) ({}):(i32)->i32 return %r:i32 }}','target successor needs 0'),
        ('wrong-entry','module {func.func @bad(%a:i32)->i32 { %r="my.scope"(%a) ({^bb0(%x:i64): %c=arith.constant 7:i32 my.yield %c:i32}):(i32)->i32 return %r:i32 }}','should match input type'),
        ('capture',(PROJECT/'scope.mlir').read_text().replace('arith.addi %x, %c2','arith.addi %c5, %c2'),'using value defined outside')]:
        p=out/(name+'.mlir');p.write_text(src)
        r=e.run('reject-'+name,[BUILD/'my-opt',p],1);e.check('diagnostic-'+name,needle in r.stderr)
    variant=(PROJECT/'scope.mlir').read_text().replace('@scope_constant()', '@scope_parameter(%arg: i32)').replace('"my.scope"(%c5)','"my.scope"(%arg)')
    p=out/'parameter.mlir';p.write_text(variant)
    r=e.run('nonconstant-scope',[BUILD/'my-opt',p,'--sccp','--canonicalize'])
    e.check('nonconstant-preserved','my.scope' in r.stdout and 'arith.addi' in r.stdout)
    docroot=WORKSPACE/'blog/docs/notes/compile/mlir/compiler'
    docs=[docroot/'memory/custom_operations.md',docroot/'ir_definition/type_shape_inference.md',docroot/'ir_definition/region_interfaces.md']
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    failed=[c['name'] for c in e.checks if not c['passed']]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261','scope':'External bufferizable model, actual one-shot decisions and CPU 4-case array checks with ownership; generated inference, dynamic/static reification; custom region propagation and actual inliner/SCCP; no generic shape proof or custom region native lowering.','files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed');print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))
if __name__=='__main__':main()
