// RUN: %my-opt %s --my-reject-marked-mul --verify-diagnostics
module {
  func.func @marked(%x:i32,%y:i32)->i32 {
    // expected-error @+1 {{teaching restriction: marked multiply is unsupported}}
    %m=arith.muli %x,%y {my.trigger}:i32
    return %m:i32
  }
}
