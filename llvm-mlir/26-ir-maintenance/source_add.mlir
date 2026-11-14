module {
 func.func @zero(%x:i32)->i32{
  %z=arith.constant 0:i32
  %r=arith.addi %x,%z:i32
  return %r:i32
 }
 func.func @general(%x:i32,%y:i32)->i32{
  %r=arith.addi %x,%y:i32
  return %r:i32
 }
}
