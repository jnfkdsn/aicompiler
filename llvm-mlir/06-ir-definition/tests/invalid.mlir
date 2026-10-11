// type-bounds
module {
// expected-error@+1 {{expected ordered bounds}}
  func.func @clip(%x: i32) -> !my.range<8, 7> {
    %r = my.limit %x bounds(#my.bounds<-4, 7>) : !my.range<8, 7>
    return %r : !my.range<8, 7>
  }
}

// -----

// attr-bounds
module {
  func.func @clip(%x: i32) -> !my.range<-4, 7> {
// expected-error@+1 {{expected ordered bounds}}
    %r = my.limit %x bounds(#my.bounds<8, 7>) : !my.range<-4, 7>
    return %r : !my.range<-4, 7>
  }
}

// -----

// attr-i32-overflow
module {
  func.func @clip(%x: i32) -> !my.range<-4, 7> {
// expected-error@+1 {{expected ordered bounds}}
    %r = my.limit %x bounds(#my.bounds<-4, 2147483648>) : !my.range<-4, 7>
    return %r : !my.range<-4, 7>
  }
}

// -----

// type-i32-underflow
module {
// expected-error@+1 {{expected ordered bounds}}
  func.func @clip(%x: i32) -> !my.range<-2147483649, 7> {
    %r = my.limit %x bounds(#my.bounds<-4, 7>) : !my.range<-2147483649, 7>
    return %r : !my.range<-2147483649, 7>
  }
}

// -----

// limit-mismatch
module {
  func.func @clip(%x: i32) -> !my.range<-4, 8> {
// expected-error@+1 {{result range must match bounds attribute}}
    %r = my.limit %x bounds(#my.bounds<-4, 7>) : !my.range<-4, 8>
    return %r : !my.range<-4, 8>
  }
}

// -----

// scope-entry
module {
  func.func @clip_inside(%x: i32) -> !my.range<-4, 7> {
// expected-error@+1 {{entry argument types must match input types}}
    %r = "my.scope"(%x) ({
    ^bb0(%local: i32, %extra: i64):
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

// -----

// scope-exit
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
// expected-error@+1 {{yield types must match result types}}
    %r:2 = "my.scope"(%x, %y) ({
    ^bb0(%a: i32, %b: i64):
      my.yield %a, %b : i32, i64
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

// -----

// scope-capture
module {
  func.func @clip_inside(%x: i32) -> !my.range<-4, 7> {
// expected-note@+1 {{required by region isolation constraints}}
    %r = "my.scope"(%x) ({
    ^bb0(%local: i32):
// expected-error@+1 {{using value defined outside the region}}
      %clipped = my.limit %x bounds(#my.bounds<-4, 7>) : !my.range<-4, 7>
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

// -----

// scope-empty-region
module {
// expected-error@+1 {{requires a nonempty body}}
  "my.scope"() ({}) : () -> ()
}

// -----

// scope-two-blocks
module {
// expected-error@+1 {{expects region #0 to have 0 or 1 blocks}}
  "my.scope"() ({
    my.yield
  ^bb1:
    my.yield
  }) : () -> ()
}

// -----

// wrong-yield-parent
module {
// expected-error@+1 {{expects parent op 'my.scope'}}
  my.yield
}

// -----

// scope-wrong-terminator
module {
  func.func @bad() {
    "my.scope"() ({
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
    %r = my.identity different %x {tag = "demo"} : i32
    return %r : i32
  }
}

// -----

// identity-type
module {
  func.func @same(%x: i64) -> i64 {
// expected-error@+1 {{operand #0 must be 32-bit signless integer}}
    %r = my.identity same %x {tag = "demo"} : i64
    return %r : i64
  }
}

// -----

// return-no-subtyping
module {
  func.func @bad(%x: !my.range<-4, 7>) -> !my.range<-4, 8> {
// expected-error@+1 {{type of return operand 0}}
    return %x : !my.range<-4, 7>
  }
}
