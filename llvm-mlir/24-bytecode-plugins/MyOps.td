include "mlir/IR/OpBase.td"
include "mlir/Interfaces/SideEffectInterfaces.td"
def My_Dialect : Dialect {
 let name="my";
 let cppNamespace="::mlir::my";
 // Keep this version exercise focused on dialect IR upgrades, not property codecs.
 let usePropertiesForAttributes=0;
}
class My_Op<string mnemonic, list<Trait> traits=[]> : Op<My_Dialect,mnemonic,traits>;
def ShiftOp : My_Op<"shift",[Pure]> {
 let summary="Add a signed i32 offset with wraparound";
 let arguments=(ins I32:$input, OptionalAttr<I64Attr>:$bias,
                            OptionalAttr<I64Attr>:$offset);
 let results=(outs I32:$result);
 let assemblyFormat="$input attr-dict `:` type($result)";
 let hasVerifier=1;
}
