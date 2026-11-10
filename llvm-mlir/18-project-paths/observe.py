#!/usr/bin/env python3
"""Locate a finite producer/consumer chain in pinned, read-only upstream sources."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo
PROJECT=Path(__file__).resolve().parent
WORKSPACE=PROJECT.parents[2]
SOURCES=json.loads((PROJECT/'source_map.json').read_text())

def audit(selected,show=True):
    report={'kind':'source inspection only; no project build, importer or device execution','projects':{}}
    failed=[]
    for name in selected:
        spec=SOURCES[name];root=WORKSPACE/'upstream'/spec['directory']
        commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        if commit!=spec['commit']:failed.append(name+' commit differs')
        if 'llvm_file' in spec:llvm=(root/spec['llvm_file']).read_text().strip()
        else:
            entry=subprocess.check_output(['git','-C',str(root),'ls-tree','HEAD',spec['llvm_gitlink']],text=True)
            llvm=entry.split()[2] if entry else 'missing gitlink'
        if llvm!=spec['llvm']:failed.append(name+' LLVM differs')
        for path,expected in spec.get('dependencies',{}).items():
            entry=subprocess.check_output(['git','-C',str(root),'ls-tree','HEAD',path],text=True)
            if not entry or entry.split()[2]!=expected:failed.append(name+' dependency differs: '+path)
        record={'dependencies':spec.get('dependencies',{}),'commit':commit,'llvm':llvm,'steps':[]};report['projects'][name]=record
        if show:print(f'\n{name}: {commit}\nLLVM dependency: {llvm}')
        for title,path,anchors in spec['steps']:
            file=root/path;content=file.read_text();lines=content.splitlines()
            step={'title':title,'path':path,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'anchors':{}}
            record['steps'].append(step)
            if show:print('\n'+title+'\n'+path)
            for anchor in anchors:
                line=next((i for i,text in enumerate(lines) if anchor in text),None)
                step['anchors'][anchor]=None if line is None else line+1
                if line is None:failed.append(name+': missing '+anchor)
                elif show:
                    for i in range(max(0,line-1),min(len(lines),line+4)):print(f'{i+1:5d} {lines[i]}')
    report['failures']=failed
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',choices=[*SOURCES,'all'],default='torch')
    parser.add_argument('--check',action='store_true',help='save source evidence; do not run these projects')
    args=parser.parse_args()
    selected=list(SOURCES) if args.project=='all' else [args.project]
    report=audit(selected,show=not args.check)
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-%H%M%S-%f')
    out=WORKSPACE/'artifacts/logs/mlir-docs'/(stamp+'-project-sources');out.mkdir(parents=True)
    report['date']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    docs=[WORKSPACE/'blog/docs/notes/compile/triton/ascend_compiler_path.md',WORKSPACE/'blog/docs/notes/compile/mlir/tutorials/pipelines/frontend.md',
          WORKSPACE/'blog/docs/notes/compile/triton/compiler_path.md',
          WORKSPACE/'blog/docs/notes/compile/npu-ir/source_path.md']
    report['documents_sha256']={str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in docs}
    (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'\n{len(selected)} source snapshots; {sum(len(v["steps"]) for v in report["projects"].values())} stages; build/run: not performed')
    print(out/'manifest.json')
    if report['failures']:raise SystemExit('\n'.join(report['failures']))

if __name__=='__main__':main()
