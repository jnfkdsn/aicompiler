// RUN: %lab-opt %s --pass-pipeline='builtin.module(func.func(lab-expand-clamp))' --verify-each | %FileCheck %s
// CHECK-LABEL: func.func @clip(
// CHECK-SAME: %[[X:.*]]: i32
// CHECK-NEXT: %[[LO:.*]] = arith.constant -4 : i32
// CHECK-NEXT: %[[HI:.*]] = arith.constant 7 : i32
// CHECK-NEXT: %[[A:.*]] = arith.maxsi %[[X]], %[[LO]] : i32
// CHECK-NEXT: %[[B:.*]] = arith.minsi %[[A]], %[[HI]] : i32
// CHECK-NEXT: %[[SUM:.*]] = arith.addi %[[B]], %[[B]] : i32
// CHECK-NEXT: return %[[B]], %[[SUM]] : i32, i32
func.func @clip(%x: i32) -> (i32, i32) {
 %r = lab.clamp %x bounds(-4, 7) : i32
 %sum = arith.addi %r, %r : i32
 return %r, %sum : i32, i32
}
