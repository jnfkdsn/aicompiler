#!/usr/bin/env python3
"""Check same-cause reduction, replay, regression checks and tool protocol."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/22-debug-testing'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,BUILD,LLVM,log_directory

def main():
    out=log_directory();e=Experiment(out);e.build();e.observe()
    e.check('version','20.1.8' in e.run('version',[LLVM/'bin/mlir-opt','--version']).stdout)
    r=e.run('accepted',[BUILD/'my-opt',PROJECT/'tests/accept.mlir','--my-reject-marked-mul'])
    good=out/'accepted.mlir';good.write_text(r.stdout)
    e.run('filecheck-good',[LLVM/'bin/FileCheck',PROJECT/'tests/accept.mlir','--input-file',good])
    bad=out/'wrong-return.mlir';bad.write_text(r.stdout.replace('return %0 : i32','return %arg0 : i32',1))
    e.check('negative-changes-return',bad.read_text()!=good.read_text())
    r=e.run('filecheck-rejects-dataflow',[LLVM/'bin/FileCheck',PROJECT/'tests/accept.mlir','--input-file',bad],1)
    e.check('negative-check-location','CHECK-NEXT' in r.stderr)
    lsp=json.loads((out/'lsp.stdout.txt').read_text())
    e.check('lsp-definition',lsp['capabilities']['definitionProvider'])
    docs=[WORKSPACE/'blog/docs/notes/compile/mlir/guides'/n for n in ['debugging.md','regression_tests.md','numerics_performance.md']]
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.rglob('*') if p.is_file() and '__pycache__' not in p.parts)]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261','scope':'Deliberate pass failure, IR/reproducer replay, same-cause reduction, instrumentation/statistics, two lit tests and FileCheck dataflow negative, LSP handshake. No debugger session, IDE integration or new kernel timings.','files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed');print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))
if __name__=='__main__':main()
