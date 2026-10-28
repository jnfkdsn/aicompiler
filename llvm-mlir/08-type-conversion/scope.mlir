module {
  func.func @scoped(%x: i32) -> !my.range<-4, 7> {
    %r = my.limit %x bounds(#my.bounds<-4, 7>) : !my.range<-4, 7>
    %s = "my.scope"(%r) ({
    ^bb0(%local: !my.range<-4, 7>):
      my.yield %local : !my.range<-4, 7>
    }) : (!my.range<-4, 7>) -> !my.range<-4, 7>
    return %s : !my.range<-4, 7>
  }
}
