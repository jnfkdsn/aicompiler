#ifndef MY_STORAGE_OPS
#define MY_STORAGE_OPS
include "mlir/IR/OpBase.td"
include "mlir/IR/AttrTypeBase.td"
include "mlir/Interfaces/SideEffectInterfaces.td"
def My_Dialect : Dialect {
  let name = "my";
  let cppNamespace = "::mlir::my";
  let useDefaultTypePrinterParser = 1;
  let useDefaultAttributePrinterParser = 1;
  let usePropertiesForAttributes = 1;
}
def TileInfo : TypeInterface<"TileInfo"> {
  let cppNamespace = "::mlir::my";
  let methods = [InterfaceMethod<"Contiguous f32 payload bytes; excludes alignment padding",
    "int64_t", "getPayloadBytes">];
}
def AlignmentPolicy : AttrInterface<"AlignmentPolicy"> {
  let cppNamespace = "::mlir::my";
  let methods = [InterfaceMethod<"Required byte alignment for the teaching planner",
    "int64_t", "getRequiredAlignment">];
}
def TileType : TypeDef<My_Dialect, "Tile", [DeclareTypeInterfaceMethods<TileInfo>]> {
  let mnemonic = "tile";
  let parameters = (ins ArrayRefParameter<"int64_t">:$shape);
  let assemblyFormat = "`<` `[` $shape `]` `>`";
  let genVerifyDecl = 1;
}
def AlignmentAttr : AttrDef<My_Dialect, "Alignment", [DeclareAttrInterfaceMethods<AlignmentPolicy>]> {
  let mnemonic = "alignment";
  let parameters = (ins "int64_t":$alignment);
  let assemblyFormat = "`<` $alignment `>`";
  let genVerifyDecl = 1;
}
def WeightedSumOp : Op<My_Dialect, "weighted_sum", [Pure, AttrSizedOperandSegments]> {
  let arguments = (ins Variadic<I32>:$inputs, Variadic<I32>:$weights, Optional<I32>:$seed);
  let results = (outs I32:$result);
  let hasVerifier = 1;
  let assemblyFormat = "`inputs` `(` $inputs `)` `weights` `(` $weights `)` (`seed` $seed^)? attr-dict";
}
def GroupSumOp : Op<My_Dialect, "group_sum", [Pure]> {
  let arguments = (ins VariadicOfVariadic<I32, "groupSizes">:$groups, DenseI32ArrayAttr:$groupSizes);
  let results = (outs Variadic<I32>:$results);
  let hasVerifier = 1;
}
#endif
