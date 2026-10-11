module {
  func.func @clip(%x: i32) -> i32 {
    %r = my.clamp %x bounds(-4, 7) : i32
    return %r : i32
  }
}
