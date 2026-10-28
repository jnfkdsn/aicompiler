module {
  func.func @clip_then_add(%x: i32) -> i32 {
    %r = my.clamp %x bounds(-4, 7) : i32
    %s = arith.addi %r, %x : i32
    return %s : i32
  }
}
