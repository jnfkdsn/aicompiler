module {
  func.func @twice(%x: i32) -> i32 {
    %zero = arith.constant 0 : i32
    %a = arith.addi %x, %zero : i32
    %b = arith.addi %x, %zero : i32
    %r = arith.addi %a, %b : i32
    return %r : i32
  }
}
