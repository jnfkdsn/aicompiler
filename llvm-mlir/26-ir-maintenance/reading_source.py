"""A finite source chain. Print only the part needed to explain add-zero."""
import hashlib
import json
from pathlib import Path
import subprocess
WORKSPACE=Path(__file__).resolve().parents[3]
SOURCE=WORKSPACE/'upstream/llvm-project'
BUILD=WORKSPACE/'artifacts/builds/mlir-20.1.8'
STAGES=[
 ('operation contract',SOURCE/'mlir/include/mlir/Dialect/Arith/IR/ArithOps.td','def Arith_AddIOp',31),
 ('generated C++ class',BUILD/'tools/mlir/include/mlir/Dialect/Arith/IR/ArithOps.h.inc','class AddIOp :',18),
 ('fold result',SOURCE/'mlir/lib/Dialect/Arith/IR/ArithOps.cpp','OpFoldResult arith::AddIOp::fold',20),
 ('pass dispatch',SOURCE/'mlir/lib/Transforms/Canonicalizer.cpp','void runOnOperation() override',9),
 ('driver consumer',SOURCE/'mlir/lib/Transforms/Utils/GreedyPatternRewriteDriver.cpp','if (config.fold &&',42),
 ('conversion registration',SOURCE/'mlir/lib/Conversion/ArithToLLVM/ArithToLLVM.cpp','using AddIOpLowering',4),
 ('regression context',SOURCE/'mlir/test/Dialect/Arith/canonicalize.mlir','addi',10),
]
def inspect(out=None,show=True):
    commit=subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()
    assert commit=='87f0227cb60147a26a1eeb4fb06e3b505e9c7261'
    records=[]
    for name,p,anchor,length in STAGES:
        source=p.read_text();assert anchor in source,(name,anchor)
        start=source[:source.index(anchor)].count('\n');lines=source.splitlines()[start:start+length]
        record={'stage':name,'file':str(p.relative_to(WORKSPACE)),'line':start+1,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'excerpt':'\n'.join(lines)};records.append(record)
        if show:print('\n'+name+': '+record['file']+':'+str(start+1)+'\n'+record['excerpt'])
    if out:(out/'source-chain.json').write_text(json.dumps({'commit':commit,'stages':records},ensure_ascii=False,indent=2)+'\n')
    return records
if __name__=='__main__':inspect()
