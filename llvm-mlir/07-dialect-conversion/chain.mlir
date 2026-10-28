module {
  func.func @twice(%x: i32) -> i32 {
    %a = my.clamp %x bounds(-4, 7) : i32
    %b = my.clamp %a bounds(-2, 3) : i32
    %r = arith.maxsi %a, %b : i32
    return %r : i32
  }
}
