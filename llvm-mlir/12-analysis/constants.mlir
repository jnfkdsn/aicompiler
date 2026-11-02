module {
  func.func @propagate(%flag: i1, %x: i32) -> i32 {
    %c3 = arith.constant 3 : i32
    %c4 = arith.constant 4 : i32
    %sum = arith.addi %c3, %c4 : i32
    %r = scf.if %flag -> i32 {
      scf.yield %sum : i32
    } else {
      %c7 = arith.constant 7 : i32
      scf.yield %c7 : i32
    }
    %out = arith.addi %r, %x : i32
    return %out : i32
  }
}
