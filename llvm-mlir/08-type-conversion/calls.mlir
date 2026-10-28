module {
  func.func @keep(%v: !my.range<-4, 7>) -> !my.range<-4, 7> {
    return %v : !my.range<-4, 7>
  }
  func.func @caller(%x: i32) -> !my.range<-4, 7> {
    %r = my.limit %x bounds(#my.bounds<-4, 7>) : !my.range<-4, 7>
    %s = func.call @keep(%r) : (!my.range<-4, 7>) -> !my.range<-4, 7>
    return %s : !my.range<-4, 7>
  }
}
