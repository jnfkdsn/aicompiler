module {
 func.func private @leaf(%x:i32)->i32 {return %x:i32}
 func.func private @helper(%flag:i1,%x:i32)->i32 {
  %one=arith.constant 1:i32
  cf.cond_br %flag,^yes,^no
  ^yes:
   %v=scf.if %flag ->i32 {
    %a=arith.addi %x,%one:i32
    scf.yield %a:i32
   } else {scf.yield %x:i32}
   cf.br ^merge(%v:i32)
  ^no:
   %b=arith.subi %x,%one:i32
   cf.br ^merge(%b:i32)
  ^merge(%m:i32):
   %r=func.call @leaf(%m):(i32)->i32
   return %r:i32
 }
 func.func @caller(%flag:i1,%x:i32)->i32 {
  %r=func.call @helper(%flag,%x):(i1,i32)->i32
  return %r:i32
 }
 func.func @effects(%src:memref<4xi32>,%dst:memref<4xi32>){
  %local=memref.alloca():memref<4xi32>
  memref.copy %src,%dst:memref<4xi32> to memref<4xi32>
  return
 }
}
