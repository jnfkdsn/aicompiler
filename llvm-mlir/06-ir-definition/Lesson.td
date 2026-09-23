#ifndef LESSON_TD
#define LESSON_TD
include "mlir/IR/OpBase.td"
include "mlir/IR/AttrTypeBase.td"
include "mlir/Interfaces/SideEffectInterfaces.td"
def Lesson_Dialect : Dialect {
 let name = "lesson";
 let cppNamespace = "::mlir::lesson";
 let useDefaultTypePrinterParser = 1;
 let useDefaultAttributePrinterParser = 1;
}
// BEGIN: bounds-interface
def StaticBounds : OpInterface<"StaticBounds"> {
 let cppNamespace = "::mlir::lesson";
 let methods = [
  InterfaceMethod<"Inclusive signed lower bound of the result.", "int64_t", "getMinimum">,
  InterfaceMethod<"Inclusive signed upper bound of the result.", "int64_t", "getMaximum">
 ];
}
// END: bounds-interface
// BEGIN: direct-op
def ClampOp : Op<Lesson_Dialect, "clamp", [Pure, DeclareOpInterfaceMethods<StaticBounds>]> {
 let arguments = (ins I32:$input, I32Attr:$lower, I32Attr:$upper);
 let results = (outs I32:$result);
 let assemblyFormat = "$input `bounds` `(` $lower `,` $upper `)` attr-dict `:` type($result)";
 let hasVerifier = 1;
}
// END: direct-op
// BEGIN: range-type
def RangeType : TypeDef<Lesson_Dialect, "Range"> {
 let mnemonic = "range";
 let parameters = (ins "int64_t":$lower, "int64_t":$upper);
 let assemblyFormat = "`<` $lower `,` $upper `>`";
 let genVerifyDecl = 1;
}
// END: range-type
// BEGIN: bounds-attr
def BoundsAttr : AttrDef<Lesson_Dialect, "Bounds"> {
 let mnemonic = "bounds";
 let parameters = (ins "int64_t":$lower, "int64_t":$upper);
 let assemblyFormat = "`<` $lower `,` $upper `>`";
 let genVerifyDecl = 1;
}
// END: bounds-attr
// BEGIN: limit-op
def LimitOp : Op<Lesson_Dialect, "limit", [Pure, DeclareOpInterfaceMethods<StaticBounds>]> {
 let summary = "Clamp an i32 and return a range-refined integer value";
 let arguments = (ins I32:$input, BoundsAttr:$bounds);
 let results = (outs RangeType:$result);
 let assemblyFormat = "$input `bounds` `(` $bounds `)` attr-dict `:` type($result)";
 let hasVerifier = 1;
}
// END: limit-op
// A deliberately conservative representation of the same scalar clamp semantics.
def OpaqueClampOp : Op<Lesson_Dialect, "opaque_clamp"> {
 let arguments = (ins I32:$input, I32Attr:$lower, I32Attr:$upper);
 let results = (outs I32:$result);
 let hasVerifier = 1;
}
// BEGIN: scope-ops
def ScopeOp : Op<Lesson_Dialect, "scope", [SingleBlock, IsolatedFromAbove, RecursiveMemoryEffects]> {
 let arguments = (ins Variadic<AnyType>:$inputs);
 let results = (outs Variadic<AnyType>:$outputs);
 let regions = (region AnyRegion:$body);
 let hasVerifier = 1;
 let hasRegionVerifier = 1;
}
def YieldOp : Op<Lesson_Dialect, "yield", [Pure, Terminator, HasParent<"ScopeOp">]> {
 let arguments = (ins Variadic<AnyType>:$values);
 let assemblyFormat = "attr-dict ($values^ `:` type($values))?";
}
// END: scope-ops
// BEGIN: manual-op
def IdentityOp : Op<Lesson_Dialect, "identity", [Pure]> {
 let arguments = (ins I32:$input);
 let results = (outs I32:$result);
 let hasCustomAssemblyFormat = 1;
}
// END: manual-op
#endif
