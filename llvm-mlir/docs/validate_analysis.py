#!/usr/bin/env python3
"""Author checks: real analysis facts, invalidation, IR legality and CPU results."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

WORKSPACE = Path(__file__).resolve().parents[3]
PROJECT = WORKSPACE/'aicompiler-labs/llvm-mlir/12-analysis'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment, LLVM, OPT, INSPECT, OPTIMIZE, log_directory


def function(text, name):
    return text.split('func.func @'+name+'(',1)[1].split('\n  func.func ',1)[0]


def main():
    out=log_directory(); e=Experiment(out); e.build()
    e.check('version','20.1.8' in e.run('version',[OPT,'--version']).stdout)
    docs=list((WORKSPACE/'blog/docs/notes/compile/mlir/compiler/analysis').glob('*.md'))
    examples,shown={},{}
    for doc in docs:
        for kind,name,code in re.findall(r'<!-- analysis-(example|output): ([\w-]+) -->\s*```text\n(.*?)\n```',doc.read_text(),re.S):
            (examples if kind=='example' else shown)[name]=code.strip()
    e.check('shown-input-coverage',set(examples)=={'dominance','constants'})
    for name,code in examples.items():
        e.check('shown-input-'+name,code==(PROJECT/(name+'.mlir')).read_text().strip())
    for p in PROJECT.glob('*.mlir'):
        normal=e.artifact('parse-'+p.stem,[OPT,p])
        generic=e.artifact('generic-'+p.stem,[OPT,p,'--mlir-print-op-generic'])
        reparse=e.artifact('reparse-'+p.stem,[OPT,generic])
        e.check('roundtrip-'+p.stem,normal.read_text()==reparse.read_text())
    facts={}
    for mode,fixture in [('dominance','dominance'),('cfg','cfg'),('alias','alias'),('constants','constants'),
                          ('ranges','ranges'),('cache','dominance'),('stale','dominance'),('calls','calls')]:
        facts[mode]=e.query(mode,PROJECT/(fixture+'.mlir'))
    expected={
        'dominance':['base dominates local: 1','local dominates return: 0','if result dominates return: 1',
                     'base dead after if: 1','if result dead after if: 0'],
        'cfg':['entry dominates join: 1','then dominates join: 0','join postdominates then: 1','then postdominates entry: 0'],
        'alias':['arguments p/q: MayAlias','allocations a/b: NoAlias','same value a/a: MustAlias',
                 'views left/right: MustAlias','store(a) vs a: Mod','store(a) vs b: NoModRef'],
        'constants':['sum: 7 : i32','if result: 7 : i32','out: unknown'],
        'ranges':['i: 0..3','next: 1..4']}
    for mode,lines in expected.items(): e.check('facts-'+mode,facts[mode].splitlines()==lines)
    e.check('cache-recomputed',facts['cache'].count('build ')==2 and 'cached=10 fresh=10 stale=0' in facts['cache'])
    e.check('wrong-preserve-is-stale',facts['stale'].count('build ')==1 and 'cached=9 fresh=10 stale=1' in facts['stale'])
    e.check('call-graph-boundary','sym_name = "entry"' in facts['calls'] and 'sym_name = "helper"' in facts['calls']
            and 'Unknown-Callee-Node' in facts['calls'])
    constants_optimized=e.artifact('constants-optimized',[OPT,PROJECT/'constants.mlir','--sccp','--canonicalize','--verify-each'])
    facts['constants-optimized']=constants_optimized.read_text()
    e.check('shown-output-coverage',set(shown)=={'cache','stale','constants','ranges','constants-optimized'})
    for name,code in shown.items(): e.check('shown-output-'+name,code==facts[name].strip())
    # Region results merge two executable paths; a dead path must not pollute the join.
    conflict=out/'constants-conflict.mlir'
    conflict.write_text((PROJECT/'constants.mlir').read_text().replace('constant 7','constant 8'))
    conflict_facts=e.query('constants',conflict,'constant-conflict')
    e.check('different-branches-unknown','if result: unknown' in conflict_facts)
    constant_true=out/'constants-true.mlir'
    constant_true.write_text(conflict.read_text().replace('%r = scf.if %flag',
        '%yes = arith.constant true\n    %r = scf.if %yes'))
    true_facts=e.query('constants',constant_true,'constant-true')
    e.check('unreachable-branch-excluded','if result: 7 : i32' in true_facts)
    invalid=out/'invalid-dominance.mlir'
    invalid.write_text((PROJECT/'cfg.mlir').read_text().replace('return %v','return %twice'))
    rejected=e.run('reject-dominance',[OPT,invalid],expected=1)
    e.check('dominance-diagnostic','does not dominate' in rejected.stderr)
    optimized=e.artifact('optimized',[OPT,PROJECT/'optimizations.mlir',*OPTIMIZE,'--verify-each']).read_text()
    pure=function(optimized,'pure'); pair=function(optimized,'load_pair'); store=function(optimized,'load_store')
    hoist=function(optimized,'hoist'); div=function(optimized,'do_not_hoist_div')
    e.check('pure-cse-and-dce',pure.count('arith.addi')==2 and 'arith.muli' not in pure)
    e.check('readonly-cse',pair.count('memref.load')==1)
    e.check('store-prevents-load-cse',store.count('memref.load')==2 and store.count('memref.store')==1)
    e.check('invariant-hoisted',hoist.index('arith.addi')<hoist.index('scf.for') and hoist.count('arith.addi')==2)
    e.check('unsafe-speculation-blocked',div.index('arith.divsi')>div.index('scf.for'))
    # The complete function excerpts in the final article must match tested input or output.
    article=(WORKSPACE/'blog/docs/notes/compile/mlir/compiler/analysis/legality.md').read_text()
    full_functions=re.findall(r'```text\n(func\.func .*?\n\})\n```',article,re.S)
    e.check('complete-function-excerpt-count',len(full_functions)==3)
    for i,code in enumerate(full_functions):
        p=out/f'article-function-{i}.mlir';p.write_text(code+'\n')
        e.run('parse-article-'+str(i),[OPT,p])
    e.native()
    e.run('observe-entry',[sys.executable,PROJECT/'observe.py','--topic','cache'])
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'scope':'Actual Dominance/PostDominance/Liveness/Alias/ModRef/CallGraph and dataflow facts; analysis preservation negative; 7 IR roundtrips; shown outputs; CSE/LICM structural checks; 15 C observations on each of before/after modules. No UB execution or performance claim.',
        'files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed; 15 native observations before + 15 after')
    print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))


if __name__=='__main__':main()
