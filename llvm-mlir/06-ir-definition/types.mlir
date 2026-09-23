module {
  func.func @clip(%x: i32) -> !lesson.range<-4, 7> {
    %r = lesson.limit %x bounds(#lesson.bounds<-4, 7>) : !lesson.range<-4, 7>
    return %r : !lesson.range<-4, 7>
  }
}
