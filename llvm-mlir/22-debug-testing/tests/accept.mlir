// RUN: %my-opt %s --my-reject-marked-mul | %FileCheck %s
// CHECK-LABEL: func.func @unmarked(
// CHECK-SAME: %[[X:.*]]: i32, %[[Y:.*]]: i32
// CHECK: %[[M:.*]] = arith.muli %[[X]], %[[Y]] : i32
// CHECK-NEXT: return %[[M]] : i32
// CHECK-LABEL: func.func @unrelated_mark(
// CHECK: arith.addi
module {
  func.func @unmarked(%x:i32,%y:i32)->i32 {
    %m=arith.muli %x,%y:i32
    return %m:i32
  }
  func.func @unrelated_mark(%x:i32,%y:i32)->i32 {
    %a=arith.addi %x,%y {my.trigger}:i32
    return %a:i32
  }
}
