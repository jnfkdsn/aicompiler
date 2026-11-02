#!/usr/bin/env python3
"""Verify scalar math/index contracts and two complete Softmax CPU paths."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

WORKSPACE=Path(__file__).resolve().parents[3]
PROJECT=WORKSPACE/'aicompiler-labs/llvm-mlir/13-softmax'
sys.path.insert(0,str(PROJECT))
from experiment import Experiment,LLVM,OPT,BUFFER,LOWER,log_directory

def main():
    out=log_directory();e=Experiment(out)
    e.check('version','20.1.8' in e.run('version',[OPT,'--version']).stdout)
    root=WORKSPACE/'blog/docs/notes/compile/mlir'
    docs=[*(root/'dialects/math').glob('*.md'),root/'tutorials/kernels/reduction_softmax.md',root/'tutorials/kernels/softmax_storage.md']
    examples={}
    for p in docs:
        for name,code in re.findall(r'<!-- softmax-example: ([\w-]+) -->\s*```text\n(.*?)\n```',p.read_text(),re.S):
            examples[name]=code.strip()
    e.check('example-coverage',set(examples)=={p.stem for p in PROJECT.glob('*.mlir')})
    for name,code in examples.items():
        p=PROJECT/(name+'.mlir');e.check('shown-input-'+name,p.read_text().strip()==code)
        normal=e.artifact('parse-'+name,[OPT,p]);generic=e.artifact('generic-'+name,[OPT,p,'--mlir-print-op-generic'])
        again=e.artifact('reparse-'+name,[OPT,generic]);e.check('roundtrip-'+name,normal.read_text()==again.read_text())
    buffer=e.stage('softmax','buffer').read_text()
    e.check('four-allocations',buffer.count('memref.alloc(')==4)
    e.check('four-computations',buffer.count('linalg.generic')==4)
    e.check('two-initializations',buffer.count('linalg.fill')==2)
    lifetime=e.artifact('softmax-lifetime',[OPT,PROJECT/'softmax.mlir',*BUFFER,'--buffer-deallocation-pipeline','--verify-each']).read_text()
    e.check('three-temporary-releases',lifetime.count('memref.dealloc')==3)
    row=(PROJECT/'row-softmax.mlir').read_text()
    e.check('row-no-internal-allocation','memref.alloc' not in row)
    libm=e.artifact('math-libm',[OPT,PROJECT/'math.mlir','--convert-math-to-libm']).read_text()
    e.check('libm-functions','@expf' in libm and '@expm1f' in libm and 'math.' not in libm)
    llvm=e.artifact('math-intrinsics',[OPT,PROJECT/'math.mlir','--convert-math-to-llvm','--convert-to-llvm','--reconcile-unrealized-casts']).read_text()
    piece=llvm.split('llvm.func @accurate_small_exp(',1)[1].split('llvm.func @_mlir_ciface_accurate_small_exp',1)[0]
    e.check('expm1-current-expansion','llvm.intr.exp' in piece and 'llvm.fsub' in piece)
    canonical=e.artifact('index-canonical',[OPT,PROJECT/'index.mlir','--canonicalize']).read_text()
    e.check('width-dependent-division-not-folded','index.divu' in canonical and '4294967298' in canonical)
    for width in [32,64]:
        lowered=e.artifact('index'+str(width),[OPT,PROJECT/'index.mlir',f'--convert-index-to-llvm=index-bitwidth={width}',
            f'--convert-func-to-llvm=index-bitwidth={width}','--canonicalize','--reconcile-unrealized-casts']).read_text()
        e.check('index-width-'+str(width),f'@tiles(%arg0: i{width}, %arg1: i{width}) -> i{width}' in lowered)
        fragment=lowered.split('llvm.func @width_sensitive()',1)[1].split('llvm.func @_mlir_ciface_width_sensitive',1)[0]
        e.check('index-constant-'+str(width),('4294967298' in fragment)==(width==64) and 'llvm.udiv' in fragment)
    invalid=out/'bad-exp.mlir';invalid.write_text('module { func.func @bad(%x: i32) -> i32 { %r = math.exp %x : i32\n return %r : i32 } }\n')
    r=e.run('reject-integer-exp',[OPT,invalid],expected=1)
    e.check('math-type-diagnostic','floating' in r.stderr)
    rows=e.native()
    scalar={r[1]:r for r in rows if r[0]=='scalar'}
    e.check('tiny-libm-nonzero',float(scalar['libm-expm1-tiny'][2])>0)
    e.check('tiny-llvm-zero',float(scalar['llvm-expm1-tiny'][2])==0)
    e.check('wide-integer-exact',int(scalar['tiles-wide'][2])==9223372036854775808)
    # Wrong max identity is especially exposed by large all-negative input.
    bad=out/'bad-initializer.mlir'
    bad.write_text((PROJECT/'softmax.mlir').read_text().replace('0xFF800000 : f32','0.0 : f32'))
    ir=e.artifact('bad-initializer-llvm',[OPT,bad,*BUFFER,'--buffer-deallocation-pipeline',*LOWER,'--verify-each'])
    ll=e.artifact('bad-initializer-translate',[LLVM/'bin/mlir-translate',ir,'--mlir-to-llvmir'],'.ll')
    obj=out/'bad-initializer.o'
    e.run('bad-initializer-codegen',[LLVM/'bin/llc','-O0','-filetype=obj','-relocation-model=pic',ll,'-o',obj])
    exe=out/'bad-initializer'
    e.run('bad-initializer-link',['/usr/bin/clang','-std=c11',PROJECT/'driver.c',obj,
        *(out/(n+'.o') for n in ['row-softmax','math','index','math-llvm']),'-lm','-L'+str(LLVM/'lib'),
        '-lmlir_c_runner_utils','-Wl,-rpath,'+str(LLVM/'lib'),'-o',exe])
    bad_run=e.run('bad-initializer-detected',[exe],expected=1)
    negative=[line for line in bad_run.stdout.splitlines() if line.startswith('softmax\tshift-negative\t')]
    e.check('negative-input-rejects-wrong-identity',len(negative)==2
            and negative[0].endswith('\t0') and negative[1].endswith('\t1'))
    e.run('observe-entry',[sys.executable,PROJECT/'observe.py','--example','softmax','--stage','buffer'])
    files=[*docs,Path(__file__).resolve(),*(p for p in PROJECT.iterdir() if p.is_file())]
    manifest={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'llvm_commit':'87f0227cb60147a26a1eeb4fb06e3b505e9c7261',
        'scope':'4 complete inputs, two math lowerings, 32/64 index conversion (64 native), buffer/deallocation structure, two CPU Softmax implementations against double reference on 10 conditions; wrong max initializer negative; no timing or device execution.',
        'files_sha256':{str(p.relative_to(WORKSPACE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'checks':e.checks}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    failed=[c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks)-len(failed)}/{len(e.checks)} checks passed; two implementations, 10 numeric conditions')
    print(out/'manifest.json')
    if failed:raise SystemExit('Failed: '+', '.join(failed))

if __name__=='__main__':main()
