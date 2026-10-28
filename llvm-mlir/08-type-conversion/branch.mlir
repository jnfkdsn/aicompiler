module {
  func.func @forward(%x: i32) -> !my.range<-4, 7> {
    %r = my.limit %x bounds(#my.bounds<-4, 7>) : !my.range<-4, 7>
    cf.br ^exit(%r : !my.range<-4, 7>)
  ^exit(%v: !my.range<-4, 7>):
    return %v : !my.range<-4, 7>
  }
}
