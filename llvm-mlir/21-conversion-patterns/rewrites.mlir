module {
  func.func @right(%x:i32)->i32 {
    %z=arith.constant 0:i32
    %a=my.add %x,%z:i32
    %b=my.add %a,%z:i32
    return %b:i32
  }
  func.func @left(%x:i32)->i32 {
    %z=arith.constant 0:i32
    %a=my.add %z,%x:i32
    return %a:i32
  }
  func.func @nonzero(%x:i32)->i32 {
    %c=arith.constant 3:i32
    %a=my.add %x,%c:i32
    return %a:i32
  }
}
