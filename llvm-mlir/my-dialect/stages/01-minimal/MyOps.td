#ifndef MY_OPS_TD
#define MY_OPS_TD
include "mlir/IR/OpBase.td"

def My_Dialect : Dialect {
  let name = "my";
  let cppNamespace = "::mlir::my";
}

def My_AddOp : Op<My_Dialect, "add"> {
  let summary = "Add two i32 values with wraparound semantics";
  let description = [{
    The result is the sum modulo 2^32. This stage defines representation
    and verification only; execution/lowering is introduced in a later stage.
  }];
  let arguments = (ins I32:$lhs, I32:$rhs);
  let results = (outs I32:$result);
  let assemblyFormat = "$lhs `,` $rhs attr-dict `:` type($result)";
}
#endif
