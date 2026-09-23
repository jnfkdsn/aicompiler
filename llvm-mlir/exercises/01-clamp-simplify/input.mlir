// This is the behavioral contract, not the starter's current output.
// Run check.py --stage solution after implementing Exercise.cpp.
// CHECK-LABEL: func.func @equal_positive(
// CHECK-NEXT: %[[P:.*]] = arith.constant 7 : i32
// CHECK-NEXT: return %[[P]] : i32
func.func @equal_positive(%x: i32) -> i32 {
  %r = lab.clamp %x bounds(7, 7) : i32
  return %r : i32
}

// CHECK-LABEL: func.func @equal_negative(
// CHECK-NEXT: %[[N:.*]] = arith.constant -4 : i32
// CHECK-NEXT: return %[[N]] : i32
func.func @equal_negative(%x: i32) -> i32 {
  %r = lab.clamp %x bounds(-4, -4) : i32
  return %r : i32
}

// CHECK-LABEL: func.func @ordinary(
// CHECK-SAME: %[[X:.*]]: i32
// CHECK-NEXT: %[[R:.*]] = lab.clamp %[[X]] bounds(-4, 7) : i32
// CHECK-NEXT: return %[[R]] : i32
func.func @ordinary(%x: i32) -> i32 {
  %r = lab.clamp %x bounds(-4, 7) : i32
  return %r : i32
}

// CHECK-LABEL: func.func @multiple_uses(
// CHECK-NEXT: %[[C:.*]] = arith.constant 3 : i32
// CHECK-NEXT: %[[S:.*]] = arith.addi %[[C]], %[[C]] : i32
// CHECK-NEXT: return %[[C]], %[[S]] : i32, i32
func.func @multiple_uses(%x: i32) -> (i32, i32) {
  %r = lab.clamp %x bounds(3, 3) : i32
  %sum = arith.addi %r, %r : i32
  return %r, %sum : i32, i32
}

// CHECK-LABEL: func.func private @declaration(i32) -> i32
func.func private @declaration(i32) -> i32
