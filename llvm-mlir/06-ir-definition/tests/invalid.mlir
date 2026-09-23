// type-bounds
module {
// expected-error@+1 {{expected ordered bounds}}
  func.func @clip(%x: i32) -> !lesson.range<8, 7> {
    %r = lesson.limit %x bounds(#lesson.bounds<-4, 7>) : !lesson.range<8, 7>
    return %r : !lesson.range<8, 7>
  }
}

// -----

// attr-bounds
module {
  func.func @clip(%x: i32) -> !lesson.range<-4, 7> {
// expected-error@+1 {{expected ordered bounds}}
    %r = lesson.limit %x bounds(#lesson.bounds<8, 7>) : !lesson.range<-4, 7>
    return %r : !lesson.range<-4, 7>
  }
}

// -----

// attr-i32-overflow
module {
  func.func @clip(%x: i32) -> !lesson.range<-4, 7> {
// expected-error@+1 {{expected ordered bounds}}
    %r = lesson.limit %x bounds(#lesson.bounds<-4, 2147483648>) : !lesson.range<-4, 7>
    return %r : !lesson.range<-4, 7>
  }
}

// -----

// type-i32-underflow
module {
// expected-error@+1 {{expected ordered bounds}}
  func.func @clip(%x: i32) -> !lesson.range<-2147483649, 7> {
    %r = lesson.limit %x bounds(#lesson.bounds<-4, 7>) : !lesson.range<-2147483649, 7>
    return %r : !lesson.range<-2147483649, 7>
  }
}

// -----

// limit-mismatch
module {
  func.func @clip(%x: i32) -> !lesson.range<-4, 8> {
// expected-error@+1 {{result range must match bounds attribute}}
    %r = lesson.limit %x bounds(#lesson.bounds<-4, 7>) : !lesson.range<-4, 8>
    return %r : !lesson.range<-4, 8>
  }
}

// -----

// scope-entry
module {
  func.func @clip_inside(%x: i32) -> !lesson.range<-4, 7> {
// expected-error@+1 {{entry argument types must match input types}}
    %r = "lesson.scope"(%x) ({
    ^bb0(%local: i32, %extra: i64):
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

// -----

// scope-exit
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
// expected-error@+1 {{yield types must match result types}}
    %r:2 = "lesson.scope"(%x, %y) ({
    ^bb0(%a: i32, %b: i64):
      lesson.yield %a, %b : i32, i64
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

// -----

// scope-capture
module {
  func.func @clip_inside(%x: i32) -> !lesson.range<-4, 7> {
// expected-note@+1 {{required by region isolation constraints}}
    %r = "lesson.scope"(%x) ({
    ^bb0(%local: i32):
// expected-error@+1 {{using value defined outside the region}}
      %clipped = lesson.limit %x bounds(#lesson.bounds<-4, 7>) : !lesson.range<-4, 7>
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

// -----

// scope-empty-region
module {
// expected-error@+1 {{requires a nonempty body}}
  "lesson.scope"() ({}) : () -> ()
}

// -----

// scope-two-blocks
module {
// expected-error@+1 {{expects region #0 to have 0 or 1 blocks}}
  "lesson.scope"() ({
    lesson.yield
  ^bb1:
    lesson.yield
  }) : () -> ()
}

// -----

// wrong-yield-parent
module {
// expected-error@+1 {{expects parent op 'lesson.scope'}}
  lesson.yield
}

// -----

// scope-wrong-terminator
module {
  func.func @bad() {
    "lesson.scope"() ({
// expected-error@+1 {{expects parent op 'func.func'}}
      return
    }) : () -> ()
    return
  }
}

// -----

// identity-keyword
module {
  func.func @same(%x: i32) -> i32 {
// expected-error@+1 {{expected 'same'}}
    %r = lesson.identity different %x {tag = "demo"} : i32
    return %r : i32
  }
}

// -----

// identity-type
module {
  func.func @same(%x: i64) -> i64 {
// expected-error@+1 {{operand #0 must be 32-bit signless integer}}
    %r = lesson.identity same %x {tag = "demo"} : i64
    return %r : i64
  }
}

// -----

// return-no-subtyping
module {
  func.func @bad(%x: !lesson.range<-4, 7>) -> !lesson.range<-4, 8> {
// expected-error@+1 {{type of return operand 0}}
    return %x : !lesson.range<-4, 7>
  }
}
