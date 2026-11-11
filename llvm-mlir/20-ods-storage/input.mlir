module {
  func.func @weighted() -> i32 {
    %c2 = arith.constant 2 : i32
    %c3 = arith.constant 3 : i32
    %c4 = arith.constant 4 : i32
    %c5 = arith.constant 5 : i32
    %c9 = arith.constant 9 : i32
    %r = my.weighted_sum inputs(%c2, %c3) weights(%c4, %c5) seed %c9 {my.note = "example"}
    return %r : i32
  }
  func.func @empty() -> i32 {
    %r = my.weighted_sum inputs() weights()
    return %r : i32
  }
  func.func @groups() -> (i32, i32, i32) {
    %c2 = arith.constant 2 : i32
    %c3 = arith.constant 3 : i32
    %c4 = arith.constant 4 : i32
    %r:3 = "my.group_sum"(%c2, %c3, %c4) <{groupSizes = array<i32: 2, 1, 0>}> : (i32, i32, i32) -> (i32, i32, i32)
    return %r#0, %r#1, %r#2 : i32, i32, i32
  }
  func.func private @payload(!my.tile<[2, 3]>) attributes {my.policy = #my.alignment<16>}
}
