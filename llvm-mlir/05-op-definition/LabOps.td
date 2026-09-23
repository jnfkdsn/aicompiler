#ifndef LAB_OPS
#define LAB_OPS
include "mlir/IR/OpBase.td"
include "mlir/Interfaces/SideEffectInterfaces.td"

// BEGIN: dialect
def Lab_Dialect : Dialect {
  let name = "lab";
  let cppNamespace = "::mlir::lab";
  let summary = "Operations for the MLIR learning examples";
}
// END: dialect

// BEGIN: clamp
def Lab_ClampOp : Op<Lab_Dialect, "clamp", [Pure]> {
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
