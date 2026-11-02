module {
  func.func @choose(%x: i32, %flag: i1) -> i32 {
    %one = arith.constant 1 : i32
    %base = arith.addi %x, %one : i32
    %r = scf.if %flag -> i32 {
      %local = arith.addi %base, %one : i32
      scf.yield %local : i32
    } else {
      %other = arith.subi %base, %one : i32
      scf.yield %other : i32
    }
    return %r : i32
  }
}
