"""Run with the fixed in-tree MLIR 20 Python package, not an unrelated mlir wheel."""
from mlir.ir import Context,Location,Module,InsertionPoint,IntegerType,IntegerAttr
from mlir.dialects import arith
from mlir.passmanager import PassManager
SOURCE='''module {func.func @answer()->i32 {
  %a=arith.constant 20:i32
  %b=arith.constant 22:i32
  %r=arith.addi %a,%b:i32
  return %r:i32
}}'''
with Context() as ctx, Location.unknown():
    module=Module.parse(SOURCE)
    pm=PassManager.parse('builtin.module(canonicalize)')
    pm.run(module.operation)
    print('after fold:');print(module)
    function=module.body.operations[0]
    block=function.regions[0].blocks[0]
    ret=block.operations[len(block.operations)-1]
    with InsertionPoint(ret):
        seven=arith.ConstantOp(IntegerType.get_signless(32),IntegerAttr.get(IntegerType.get_signless(32),7))
    ret.operands[0]=seven.result
    assert module.operation.verify()
    pm.run(module.operation)
    print('after replacement:');print(module)
    # Keep only the owning module for later work; do not rely on old operation
    # wrappers after an arbitrary pass or erase.
