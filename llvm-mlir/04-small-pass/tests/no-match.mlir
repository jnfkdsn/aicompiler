// RUN: %lab-opt %s --pass-pipeline='builtin.module(func.func(lab-remove-add-zero))' --verify-each | %FileCheck %s

// CHECK-LABEL: func.func @nonzero(
// CHECK-SAME: %[[X:.*]]: i32
// CHECK-NEXT: %[[C:.*]] = arith.constant 1 : i32
// CHECK-NEXT: %[[R:.*]] = arith.addi %[[X]], %[[C]] : i32
// CHECK-NEXT: return %[[R]] : i32
func.func @nonzero(%x: i32) -> i32 {
  %one = arith.constant 1 : i32
  %r = arith.addi %x, %one : i32
  return %r : i32
}

// CHECK-LABEL: func.func @left_zero(
// CHECK-SAME: %[[X:.*]]: i32
// CHECK-NEXT: %[[C:.*]] = arith.constant 0 : i32
// CHECK-NEXT: %[[R:.*]] = arith.addi %[[C]], %[[X]] : i32
// CHECK-NEXT: return %[[R]] : i32
func.func @left_zero(%x: i32) -> i32 {
  %zero = arith.constant 0 : i32
  %r = arith.addi %zero, %x : i32
  return %r : i32
}

// CHECK-LABEL: func.func @wide(
// CHECK-SAME: %[[X:.*]]: i64
// CHECK-NEXT: %[[C:.*]] = arith.constant 0 : i64
// CHECK-NEXT: %[[R:.*]] = arith.addi %[[X]], %[[C]] : i64
// CHECK-NEXT: return %[[R]] : i64
func.func @wide(%x: i64) -> i64 {
  %zero = arith.constant 0 : i64
  %r = arith.addi %x, %zero : i64
  return %r : i64
}

// CHECK-LABEL: func.func @flagged(
// CHECK-SAME: %[[X:.*]]: i32
// CHECK-NEXT: %[[C:.*]] = arith.constant 0 : i32
// CHECK-NEXT: %[[R:.*]] = arith.addi %[[X]], %[[C]] overflow<nsw> : i32
// CHECK-NEXT: return %[[R]] : i32
func.func @flagged(%x: i32) -> i32 {
  %zero = arith.constant 0 : i32
  %r = arith.addi %x, %zero overflow<nsw> : i32
  return %r : i32
}

// CHECK-LABEL: func.func @unknown_rhs(
// CHECK-SAME: %[[X:.*]]: i32, %[[Y:.*]]: i32
// CHECK-NEXT: %[[R:.*]] = arith.addi %[[X]], %[[Y]] : i32
// CHECK-NEXT: return %[[R]] : i32
func.func @unknown_rhs(%x: i32, %y: i32) -> i32 {
  %r = arith.addi %x, %y : i32
  return %r : i32
}
