module {
  func.func @clip_inside(%x: i32) -> !lesson.range<-4, 7> {
    %r = "lesson.scope"(%x) ({
    ^bb0(%local: i32):
      %clipped = lesson.limit %local bounds(#lesson.bounds<-4, 7>) : !lesson.range<-4, 7>
      lesson.yield %clipped : !lesson.range<-4, 7>
    }) : (i32) -> !lesson.range<-4, 7>
    return %r : !lesson.range<-4, 7>
  }
  func.func @swap(%x: i32, %y: i64) -> (i64, i32) {
    %r:2 = "lesson.scope"(%x, %y) ({
    ^bb0(%a: i32, %b: i64):
      lesson.yield %b, %a : i64, i32
    }) : (i32, i64) -> (i64, i32)
    return %r#0, %r#1 : i64, i32
  }
  func.func @empty() {
    "lesson.scope"() ({
      lesson.yield
    }) : () -> ()
    return
  }
}
