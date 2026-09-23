module {
  func.func @direct(%x: i32) -> i32 {
    %r = lesson.clamp %x bounds(-4, 7) : i32
    return %r : i32
  }
}
