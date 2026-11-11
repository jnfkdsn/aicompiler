module {
  func.func private @pair(%x:i32,%y:i32)->tuple<i32,i32> {
    %p=my.pack %x,%y : tuple<i32,i32>
    return %p:tuple<i32,i32>
  }
  func.func private @sum(%p:tuple<i32,i32>)->i32 {
    cf.br ^next(%p:tuple<i32,i32>)
  ^next(%q:tuple<i32,i32>):
    %x=my.first %q:tuple<i32,i32>
    %y=my.second %q:tuple<i32,i32>
    %r=arith.addi %x,%y:i32
    return %r:i32
  }
  func.func @entry(%a:i32,%b:i32)->i32 attributes {llvm.emit_c_interface} {
    %p=call @pair(%a,%b):(i32,i32)->tuple<i32,i32>
    %r=call @sum(%p):(tuple<i32,i32>)->i32
    return %r:i32
  }
  func.func @difference(%a:i32,%b:i32)->i32 attributes {llvm.emit_c_interface} {
    %p=call @pair(%a,%b):(i32,i32)->tuple<i32,i32>
    %x=my.first %p:tuple<i32,i32>
    %y=my.second %p:tuple<i32,i32>
    %r=arith.subi %x,%y:i32
    return %r:i32
  }
}
