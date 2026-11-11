#ifndef MY_EXTENSION_OPS
#define MY_EXTENSION_OPS
include "mlir/IR/OpBase.td"
include "mlir/Interfaces/SideEffectInterfaces.td"
include "mlir/Interfaces/InferTypeOpInterface.td"
include "mlir/Interfaces/ControlFlowInterfaces.td"
def My_Dialect : Dialect {
  let name = "my";
  let cppNamespace = "::mlir::my";
}
def AddOneOp : Op<My_Dialect, "add_one", [Pure, SameOperandsAndResultType,
    DeclareOpInterfaceMethods<InferTypeOpInterface>,
    DeclareOpInterfaceMethods<ReifyRankedShapedTypeOpInterface>]> {
  let summary = "Return input+1 with a fully overwritten destination candidate";
  let arguments = (ins RankedTensorOf<[F32]>:$input, RankedTensorOf<[F32]>:$init);
  let results = (outs RankedTensorOf<[F32]>:$result);
  let hasVerifier = 1;
  let assemblyFormat = "$input `outs` `(` $init `)` attr-dict `:` type($result)";
}
def ScopeOp : Op<My_Dialect, "scope", [SingleBlock, IsolatedFromAbove,
    RecursiveMemoryEffects,
    DeclareOpInterfaceMethods<RegionBranchOpInterface, ["getEntrySuccessorOperands"]>]> {
  let summary = "Execute one block exactly once, forwarding one i32 value";
  let arguments = (ins I32:$input);
  let results = (outs I32:$result);
  let regions = (region AnyRegion:$body);
  let hasRegionVerifier = 1;
}
def YieldOp : Op<My_Dialect, "yield", [Pure, ReturnLike, Terminator, HasParent<"ScopeOp">]> {
  let arguments = (ins I32:$value);
  let assemblyFormat = "$value attr-dict `:` type($value)";
}
#endif
