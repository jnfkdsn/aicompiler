module {
  func.func private @external(i32) -> i32
  func.func private @helper(%x: i32) -> i32 {
    %r = func.call @external(%x) : (i32) -> i32
    return %r : i32
  }
  func.func @entry(%x: i32) -> i32 {
    %r = func.call @helper(%x) : (i32) -> i32
    return %r : i32
  }
}
