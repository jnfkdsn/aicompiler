#!/usr/bin/env python3
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/24-bytecode-plugins'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,BUILD,LLVM,log_directory

def main():
    out=log_directory();e=Experiment(out);e.build();e.observe()
    e.check('version','20.1.8' in e.run('version',[LLVM/'bin/mlir-opt','--version']).stdout)
    for name,src,needle in [
        ('two-fields','offset=5:i64,bias=5:i64','requires only offset'),
        ('too-wide','offset=2147483648:i64','offset must fit signed i32'),
        ('missing','','requires only offset')]:
        p=out/(name+'.mlir');p.write_text((PROJECT/'v2.mlir').read_text().replace('offset=5:i64',src))
        r=e.run(name,[BUILD/'my-opt-v2',p],1);e.check(name+'-reason',needle in r.stderr)
    p=out/'negative.mlir';p.write_text((PROJECT/'v1.mlir').read_text().replace('bias=5','bias=-5'))
    bc=out/'negative.mlirbc';e.run('negative-write',[BUILD/'my-opt-v1',p,'--emit-bytecode','-o',bc])
    r=e.run('negative-upgrade',[BUILD/'my-opt-v2',bc,'--my-lower-shift','--canonicalize']);e.check('negative32','constant 32' in r.stdout)
    r=e.run('pass-not-registered',[LLVM/'bin/mlir-opt',PROJECT/'v2.mlir','--load-dialect-plugin='+str(BUILD/'MyPlugin.so'),'--pass-pipeline=builtin.module(my-plugin-mark)'],1)
    e.check('separate-registration','my-plugin-mark' in r.stderr and 'registered pass' in r.stderr)
    docs=[WORKSPACE/'blog/docs/notes/compile/mlir/guides'/n for n in ['bytecode.md','plugins.md']]
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261','scope':'Versioned my.shift bytecode upgrades bias to offset, rejects future dialect version, separates container version and text. Real Linux dialect/pass plugins, API mismatch via error-handling loader. 42/32 are IR folds, not native target execution.','files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed');print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))
if __name__=='__main__':main()
