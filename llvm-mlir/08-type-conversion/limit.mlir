module {
  func.func @clip(%x: i32) -> !my.range<-4, 7> {
    %r = my.limit %x bounds(#my.bounds<-4, 7>) : !my.range<-4, 7>
    return %r : !my.range<-4, 7>
  }
}
