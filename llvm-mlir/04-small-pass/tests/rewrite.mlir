// RUN: %lab-opt %s --pass-pipeline='builtin.module(func.func(lab-remove-add-zero))' --verify-each | %FileCheck %s
// RUN: %lab-opt %s --pass-pipeline='builtin.module(func.func(lab-remove-add-zero))' -o %t.once
// RUN: %lab-opt %t.once --pass-pipeline='builtin.module(func.func(lab-remove-add-zero))' | %FileCheck %s

// CHECK-LABEL: func.func @twice(
// CHECK-SAME: %[[X:.*]]: i32
// CHECK-NEXT: %[[SUM:.*]] = arith.addi %[[X]], %[[X]] : i32
// CHECK-NEXT: return %[[SUM]] : i32
// CHECK-NEXT: }
func.func @twice(%x: i32) -> i32 {
  %zero = arith.constant 0 : i32
  %a = arith.addi %x, %zero : i32
  %r = arith.addi %a, %x : i32
  return %r : i32
}

// All operand slots, including repeated uses in one user, must be rewired.
// CHECK-LABEL: func.func @repeated_uses(
// CHECK-SAME: %[[X:.*]]: i32
// CHECK-NEXT: %[[SUM:.*]] = arith.addi %[[X]], %[[X]] : i32
// CHECK-NEXT: return %[[X]], %[[SUM]] : i32, i32
// CHECK-NEXT: }
func.func @repeated_uses(%x: i32) -> (i32, i32) {
  %zero = arith.constant 0 : i32
  %a = arith.addi %x, %zero : i32
  %sum = arith.addi %a, %a : i32
  return %a, %sum : i32, i32
}

// CHECK-LABEL: func.func @nested(
// CHECK-SAME: %[[P:.*]]: i1, %[[X:.*]]: i32
// CHECK-NEXT: %[[R:.*]] = scf.if %[[P]] -> (i32) {
// CHECK-NEXT: scf.yield %[[X]] : i32
// CHECK-NEXT: } else {
// CHECK-NEXT: scf.yield %[[X]] : i32
// CHECK-NEXT: }
// CHECK-NEXT: return %[[R]] : i32
func.func @nested(%p: i1, %x: i32) -> i32 {
  %zero = arith.constant 0 : i32
  %r = scf.if %p -> (i32) {
    %a = arith.addi %x, %zero : i32
    scf.yield %a : i32
  } else {
    scf.yield %x : i32
  }
  return %r : i32
}

// CHECK-LABEL: func.func private @external(i32) -> i32
func.func private @external(i32) -> i32
