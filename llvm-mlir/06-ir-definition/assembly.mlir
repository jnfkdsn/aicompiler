module {
  func.func @same(%x: i32) -> i32 {
    %r = my.identity same %x {tag = "demo"} : i32
    return %r : i32
  }
}
