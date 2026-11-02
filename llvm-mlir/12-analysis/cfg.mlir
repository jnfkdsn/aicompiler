module {
  func.func @diamond(%flag: i1, %x: i32) -> i32 {
    cf.cond_br %flag, ^then, ^else
  ^then:
    %twice = arith.addi %x, %x : i32
    cf.br ^join(%twice : i32)
  ^else:
    cf.br ^join(%x : i32)
  ^join(%v: i32):
    return %v : i32
  }
}
