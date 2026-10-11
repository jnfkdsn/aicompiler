module {
  func.func @clip_inside(%x: i32) -> !my.range<-4, 7> {
    %r = "my.scope"(%x) ({
    ^bb0(%local: i32):
      %clipped = my.limit %local bounds(#my.bounds<-4, 7>) : !my.range<-4, 7>
      my.yield %clipped : !my.range<-4, 7>
    }) : (i32) -> !my.range<-4, 7>
    return %r : !my.range<-4, 7>
  }
  func.func @swap(%x: i32, %y: i64) -> (i64, i32) {
    %r:2 = "my.scope"(%x, %y) ({
    ^bb0(%a: i32, %b: i64):
      my.yield %b, %a : i64, i32
    }) : (i32, i64) -> (i64, i32)
    return %r#0, %r#1 : i64, i32
  }
  func.func @empty() {
    "my.scope"() ({
      my.yield
    }) : () -> ()
    return
  }
}
