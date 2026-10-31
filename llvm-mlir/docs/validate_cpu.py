#!/usr/bin/env python3
"""Verify CPU/LLVM articles, translation boundaries, C ABI execution and JIT."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

WORKSPACE = Path(__file__).resolve().parents[3]
PROJECT = WORKSPACE / 'aicompiler-labs/llvm-mlir/11-cpu-lowering'
sys.path.insert(0, str(PROJECT))
from experiment import Commands, LLVM, OPT, LLVM_FLAGS, log_directory


def main():
    root = WORKSPACE / 'blog/docs/notes/compile/mlir'
    docs = [*(root/'dialects/llvm').glob('*.md'), *(root/'compiler/lowering').glob('*.md'),
            root/'tutorials/pipelines/cpu.md']
    out = log_directory(); c = Commands(out)
    version = c.run('version', [OPT, '--version'])
    c.check('llvm-version', '20.1.8' in version.stdout)
    groups = {kind: {} for kind in ('example', 'output', 'llvmir', 'c')}
    for p in docs:
        for kind,name,code in re.findall(r'<!-- cpu-(example|output|llvmir|c): ([\w.-]+) -->\s*```(?:text|llvm|c)\n(.*?)\n```',p.read_text(),re.S):
            if name in groups[kind]: c.check('duplicate-'+kind+'-'+name, groups[kind][name] == code)
            groups[kind][name] = code
    examples = groups['example']
    c.check('example-coverage', set(examples) == {p.stem for p in PROJECT.glob('*.mlir')})
    for name,code in examples.items():
        fixture = PROJECT/(name+'.mlir')
        c.check('fixture-'+name,fixture.read_text().strip() == code.strip())
        p=out/(name+'-input.mlir');p.write_text(code+'\n')
        normal=c.artifact('parse-'+name,[OPT,p])
        generic=c.artifact('generic-'+name,[OPT,p,'--mlir-print-op-generic'])
        reparse=c.artifact('reparse-'+name,[OPT,generic])
        c.check('roundtrip-'+name, normal.read_text() == reparse.read_text())
    c.check('shown-output-coverage', set(groups['output']) == {'index32','add-loops','sum-cf'})
    for tag,name,stage in [('add-loops','add-into','loops'),('sum-cf','sum','cf')]:
        p=c.stage(name,stage)
        c.check('shown-'+tag,p.read_text().strip() == groups['output'][tag].strip())
    loops=(out/'add-into-loops.mlir').read_text()
    c.check('loop-structure',loops.count('scf.for')==2 and loops.count('memref.load')==2
            and loops.count('memref.store')==1 and 'linalg.' not in loops)
    index32=c.artifact('index32',[OPT,PROJECT/'index.mlir','--convert-arith-to-llvm=index-bitwidth=32',
        '--convert-func-to-llvm=index-bitwidth=32','--reconcile-unrealized-casts'])
    c.check('shown-index32',index32.read_text().strip()==groups['output']['index32'].strip())
    index64=c.stage('index','llvm')
    c.check('index-width-changes-boundary','@advance(%arg0: i32) -> i32' in index32.read_text()
            and '@advance(%arg0: i64) -> i64' in index64.read_text())
    for name,code in groups['llvmir'].items():
        translated=c.artifact('translate-shown-'+name,[LLVM/'bin/mlir-translate',PROJECT/(name+'.mlir'),'--mlir-to-llvmir'],'.ll')
        c.check('translation-'+name,translated.read_text().strip()==code.strip())
    c.check('phi-edge-values', 'phi i32' in groups['llvmir']['choose']
            and '[ %2, %5 ], [ %1, %4 ]' in groups['llvmir']['choose'])
    observations=c.native()
    read=(out/'read2d-llvm.mlir').read_text()
    c.check('c-wrapper-signature','@_mlir_ciface_read2d(%arg0: !llvm.ptr, %arg1: i64, %arg2: i64) -> i32' in read)
    c.check('descriptor-type','!llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>' in read)
    make=(out/'make-copy-llvm.mlir').read_text()
    c.check('result-out-pointer','@_mlir_ciface_make_copy(%arg0: !llvm.ptr, %arg1: !llvm.ptr)' in make
            and 'llvm.store' in make.split('@_mlir_ciface_make_copy',1)[1])
    for name,code in groups['c'].items():
        c.check('shown-c-'+name,(PROJECT/name).read_text().strip()==code.strip())
    minimal=out/'minimal'
    c.run('link-minimal',['/usr/bin/clang','-std=c11','-Wall','-Wextra','-Werror',PROJECT/'minimal_driver.c',out/'add-into.o','-o',minimal])
    result=c.run('run-minimal',[minimal])
    c.check('tutorial-six-values',result.stdout.splitlines()==['11','22','33','44','55','66'])
    jit=c.stage('jit','llvm')
    result=c.run('jit',[LLVM/'bin/mlir-runner',jit,'-e','main','-entry-point-result=i32'])
    c.check('jit-return',result.stdout.strip()=='42')
    mixed=out/'mixed.mlir'
    mixed.write_text('module { llvm.func @mixed() -> i32 { %v = arith.constant 7 : i32\n llvm.return %v : i32 } }\n')
    c.run('parse-mixed',[OPT,mixed])
    result=c.run('reject-mixed-translation',[LLVM/'bin/mlir-translate',mixed,'--mlir-to-llvmir'],expected=1)
    c.check('translator-registration-diagnostic',"Dialect `arith' not found" in result.stderr)
    generic_mixed=c.artifact('generic-mixed',[OPT,mixed,'--mlir-print-op-generic'])
    result=c.run('reject-generic-mixed',[LLVM/'bin/mlir-translate',generic_mixed,
        '--allow-unregistered-dialect','--mlir-to-llvmir'],expected=1)
    c.check('translation-interface-diagnostic','arith' in result.stderr and 'translation' in result.stderr.lower())
    repaired=c.artifact('repair-mixed',[OPT,mixed,'--convert-arith-to-llvm','--reconcile-unrealized-casts'])
    c.run('translate-repaired',[LLVM/'bin/mlir-translate',repaired,'--mlir-to-llvmir'])
    bad=out/'bad-fadd.mlir';bad.write_text(examples['pointer'].replace('llvm.add','llvm.fadd'))
    result=c.run('invalid-fadd',[OPT,bad],expected=1)
    c.check('fadd-diagnostic','floating point' in result.stderr)
    missing=out/'missing.mlir'
    missing.write_text('module { llvm.func @missing(i32) -> i32\n llvm.func @entry(%x: i32) -> i32 {\n %r = llvm.call @missing(%x) : (i32) -> i32\n llvm.return %r : i32 } }\n')
    ir=c.artifact('missing-translate',[LLVM/'bin/mlir-translate',missing,'--mlir-to-llvmir'],'.ll')
    obj=out/'missing.o'
    c.run('missing-codegen',[LLVM/'bin/llc','-filetype=obj','-relocation-model=pic',ir,'-o',obj])
    driver=out/'missing-driver.c';driver.write_text('extern int entry(int); int main(void) { return entry(3); }\n')
    result=c.run('missing-link',['/usr/bin/clang',driver,obj,'-o',out/'missing'],expected=1)
    c.check('missing-symbol-diagnostic','missing' in result.stderr and 'undefined reference' in result.stderr)
    c.run('observation-entry',[sys.executable,PROJECT/'observe.py','--example','sum','--stage','cf'])
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.glob('*') if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'scope':'8 complete inputs, exact stage/translation outputs, 33 native C ABI observations, 6 minimal tutorial values, JIT return 42, parser/translation/link failures; 32-bit index is conversion-only; no target-performance claim',
        'files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':c.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[item['name'] for item in c.checks if not item['passed']]
    print(f'{len(c.checks)-len(failed)}/{len(c.checks)} checks passed; {len(observations)} extended C observations + 6 tutorial values + JIT 42')
    print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))


if __name__=='__main__':main()
