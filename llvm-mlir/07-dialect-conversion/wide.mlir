module {
  func.func @wide(%a: i64, %b: i64) -> i64 {
    %r = arith.maxsi %a, %b : i64
    return %r : i64
  }
}
