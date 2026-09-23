func.func @bad(%x: i32) -> i32 {
  // expected-error@+1 {{requires lower <= upper (signed i32)}}
  %r = lab.clamp %x bounds(8, 7) : i32
  return %r : i32
}
