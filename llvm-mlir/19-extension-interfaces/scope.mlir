module {
  func.func @scope_constant() -> i32 {
    %c5 = arith.constant 5 : i32
    %r = "my.scope"(%c5) ({
      ^bb0(%x: i32):
        %c2 = arith.constant 2 : i32
        %sum = arith.addi %x, %c2 : i32
        my.yield %sum : i32
    }) : (i32) -> i32
    return %r : i32
  }
}
