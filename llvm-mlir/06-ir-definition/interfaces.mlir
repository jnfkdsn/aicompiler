module {
  func.func @unused(%x: i32) {
    %a = lab.clamp %x bounds(-4, 7) : i32
    %b = "lesson.opaque_clamp"(%x) <{lower = -4 : i32, upper = 7 : i32}> : (i32) -> i32
    return
  }
}
