#!/usr/bin/env python3
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/26-ir-maintenance'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,LLVM,log_directory

def main():
    out=log_directory();e=Experiment(out);e.build();e.observe()
    e.check('version','20.1.8' in e.run('version',[LLVM/'bin/mlir-opt','--version']).stdout)
    for p in PROJECT.glob('*.mlir'):
        normal=e.ir('parse-'+p.stem,p)
        e.ir('generic-'+p.stem,p,['--mlir-print-op-generic'])
        again=e.ir('again-'+p.stem,out/('generic-'+p.stem+'.mlir'))
        e.check('roundtrip-'+p.stem,normal.stdout==again.stdout)
    docs=[WORKSPACE/'blog/docs/notes/compile/mlir'/n for n in ['guides/source_reading.md','dialects/scf/regions_switch.md','dialects/scf/parallel_results.md','compiler/transforms/ir_maintenance.md','compiler/analysis/resources_effects.md']]
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261','scope':'SCF region/switch/parallel/forall with 17 CPU cases in stated supported range; known wide-index truncation is an observed limitation, not correctness. CFG clone/remap, symbol rename and guarded unknown scope, illegal move diagnostic/repair. Real memory effect queries vs synthetic protocol instances. Seven source stages and actual add folding/conversion. No device parallel execution.','known_limitations':['20.1.8 IndexSwitchLowering narrows index to i32: tag4294967296 takes case0 instead of source default','One-Shot Bufferization does not support execute_region with multiple distinct yields'],'files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed');print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))
if __name__=='__main__':main()
