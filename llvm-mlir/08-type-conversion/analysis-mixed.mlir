module {
  func.func @mixed(%x: i32) -> !my.range<-4, 7> {
    %a = my.clamp %x bounds(-8, 9) : i32
    %b = my.limit %a bounds(#my.bounds<-4, 7>) : !my.range<-4, 7>
    return %b : !my.range<-4, 7>
  }
}
