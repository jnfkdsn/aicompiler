"""Failures happen at distinct boundaries; no invalid C handles are dereferenced."""
from mlir.ir import Context,Module,MLIRError
from mlir.passmanager import PassManager
with Context():
    for label, action in [
        ('parse', lambda: Module.parse('invalid IR')),
        ('pipeline', lambda: PassManager.parse('builtin.module(no-such-pass)')),
    ]:
        try:
            action()
        except (MLIRError,ValueError) as error:
            print(label+' rejected: '+type(error).__name__)
        else:
            raise AssertionError(label+' unexpectedly accepted')
