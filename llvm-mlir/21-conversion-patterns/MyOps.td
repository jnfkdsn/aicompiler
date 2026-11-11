#ifndef MY_CONVERSION_OPS
#define MY_CONVERSION_OPS
include "mlir/IR/OpBase.td"
include "mlir/Interfaces/SideEffectInterfaces.td"
def My_Dialect : Dialect {let name="my";let cppNamespace="::mlir::my";}
def PackOp : Op<My_Dialect,"pack",[Pure]> {
 let arguments=(ins I32:$first,I32:$second);
 let results=(outs TupleOf<[I32]>:$result);
 let hasVerifier=1;
 let assemblyFormat="$first `,` $second attr-dict `:` type($result)";
}
def FirstOp : Op<My_Dialect,"first",[Pure]> {
 let arguments=(ins TupleOf<[I32]>:$input);
 let hasVerifier=1;
 let results=(outs I32:$result);
 let assemblyFormat="$input attr-dict `:` type($input)";
}
def SecondOp : Op<My_Dialect,"second",[Pure]> {
 let arguments=(ins TupleOf<[I32]>:$input);
 let hasVerifier=1;
 let results=(outs I32:$result);
 let assemblyFormat="$input attr-dict `:` type($input)";
}
def AddOp : Op<My_Dialect,"add",[Pure]> {
 let arguments=(ins I32:$lhs,I32:$rhs);
 let results=(outs I32:$result);
 let assemblyFormat="$lhs `,` $rhs attr-dict `:` type($result)";
}
#endif
