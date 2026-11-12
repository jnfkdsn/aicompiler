from mlir.ir import Context,Module
with Context():
    module=Module.parse('module {func.func @f() { %x=arith.constant 7:i32 return }}')
    function=module.body.operations[0]
    block=function.regions[0].blocks[0]
    victim=block.operations[0]
    victim.operation.erase()
    caught=False
    try:
        victim.operation.verify()
    except RuntimeError as error:
        caught=True
        print('erased wrapper rejected:',str(error))
    assert caught
    assert module.operation.verify()
# The module retains its context; leaving the with statement removes the default
# context scope, not all objects backed by that context.
print('module survives default-context scope:',module.operation.verify())
