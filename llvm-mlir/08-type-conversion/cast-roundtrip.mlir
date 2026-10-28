module {
  func.func @roundtrip(%x: i32) -> i32 {
    %r = builtin.unrealized_conversion_cast %x : i32 to !my.range<-4, 7>
    %v = builtin.unrealized_conversion_cast %r : !my.range<-4, 7> to i32
    return %v : i32
  }
}
