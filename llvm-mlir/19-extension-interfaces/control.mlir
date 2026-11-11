module {
  func.func private @choose(%flag: i1, %x: i32) -> i32 {
    %c7 = arith.constant 7 : i32
    %r = scf.if %flag -> i32 {
      scf.yield %c7 : i32
    } else {
      scf.yield %x : i32
    }
    return %r : i32
  }
  func.func @entry(%n: index) -> i32 {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %true = arith.constant true
    %c3 = arith.constant 3 : i32
    %v = call @choose(%true, %c3) : (i1, i32) -> i32
    %r = scf.for %i = %c0 to %n step %c1 iter_args(%s = %v) -> i32 {
      %next = arith.addi %s, %c3 : i32
      scf.yield %next : i32
    }
    return %r : i32
  }
}
