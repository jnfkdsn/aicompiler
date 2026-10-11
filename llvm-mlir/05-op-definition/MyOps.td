#ifndef MY_OPS
#define MY_OPS
include "mlir/IR/OpBase.td"
include "mlir/Interfaces/SideEffectInterfaces.td"

// BEGIN: dialect
def My_Dialect : Dialect {
  let name = "my";
  let cppNamespace = "::mlir::my";
  let summary = "Operations for the MLIR learning examples";
}
// END: dialect

// BEGIN: clamp
def My_ClampOp : Op<My_Dialect, "clamp", [Pure]> {
  let summary = "Clamp a signed i32 value to inclusive constant bounds";
  let description = [{
    Interpret input, lower and upper as signed 32-bit integers.
    Return lower if input < lower, upper if input > upper, otherwise input.
    Require lower <= upper. Equal bounds are valid.
  }];
  let arguments = (ins I32:$input, I32Attr:$lower, I32Attr:$upper);
  let results = (outs I32:$result);
  let assemblyFormat = [{
    $input `bounds` `(` $lower `,` $upper `)` attr-dict `:` type($input)
  }];
  let hasVerifier = 1;
}
// END: clamp
#endif
