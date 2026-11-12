#!/usr/bin/env python3
"""Validate official C and Python bindings against a common IR task."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/23-bindings'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,LLVM,PYTHON,PACKAGE,log_directory

def main():
    out=log_directory();e=Experiment(out);e.build();e.observe()
    e.check('version','20.1.8' in e.run('version',[LLVM/'bin/mlir-opt','--version']).stdout)
    e.check('python312','3.12.' in e.run('python-version',[PYTHON,'--version']).stdout)
    e.run('dependencies',[PYTHON,'-m','pip','freeze'])
    package=e.run('package-path',[PYTHON,'-c','import mlir.ir; print(mlir.ir.__file__)'],python=True)
    e.check('in-tree-package',str(PACKAGE) in package.stdout)
    docs=[WORKSPACE/'blog/docs/notes/compile/mlir/guides'/n for n in ['c_api.md','python_bindings.md']]
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261','scope':'C and official Python manipulate IR: fold42, construct7, transfer ownership, change operand, dead code cleanup; equal output and verifier, explicit erase invalidation and retained context, distinct parse/pipeline errors. No target execution or general cross-version ABI guarantee.','files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed');print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))
if __name__=='__main__':main()
