module {
  func.func @noise(%x:i32,%y:i32)->i32 {
    %a=arith.addi %x,%y:i32
    return %a:i32
  }
  func.func @hit(%x:i32,%y:i32)->i32 {
    %z=arith.constant 0:i32
    %dead=arith.addi %x,%z:i32
    %m=arith.muli %x,%y {my.trigger}:i32
    return %m:i32
  }
  func.func @other()->i32 {
    %c=arith.constant 11:i32
    return %c:i32
  }
}
