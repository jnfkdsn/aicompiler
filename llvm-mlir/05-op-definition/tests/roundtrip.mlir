// RUN: %lab-opt %s | %FileCheck %s
// RUN: %lab-opt %s --mlir-print-op-generic -o %t.generic
// RUN: %FileCheck %s --check-prefix=GENERIC < %t.generic
// RUN: %lab-opt %t.generic | %FileCheck %s
// CHECK-LABEL: func.func @clip(
// CHECK-SAME: %[[X:.*]]: i32
// CHECK-NEXT: %[[R:.*]] = lab.clamp %[[X]] bounds(-4, 7) : i32
// CHECK-NEXT: return %[[R]] : i32
// GENERIC: "lab.clamp"({{.*}}) <{lower = -4 : i32, upper = 7 : i32}> : (i32) -> i32
func.func @clip(%x: i32) -> i32 {
 %r = lab.clamp %x bounds(-4, 7) : i32
 return %r : i32
}
// CHECK-LABEL: func.func @equal(
// CHECK: lab.clamp {{.*}} bounds(-3, -3) : i32
func.func @equal(%x: i32) -> i32 {
 %r = lab.clamp %x bounds(-3, -3) : i32
 return %r : i32
}
// CHECK-LABEL: func.func @full_range(
// CHECK: lab.clamp {{.*}} bounds(-2147483648, 2147483647) : i32
func.func @full_range(%x: i32) -> i32 {
 %r = lab.clamp %x bounds(-2147483648, 2147483647) : i32
 return %r : i32
}
