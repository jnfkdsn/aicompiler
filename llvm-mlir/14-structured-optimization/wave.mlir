module {
  func.func @wave(%a: memref<5x7xi32>) attributes {llvm.emit_c_interface} {
    %one = arith.constant 1 : i32
    affine.for %i = 1 to 5 {
      affine.for %j = 0 to 6 {
        %v = affine.load %a[%i - 1, %j + 1] : memref<5x7xi32>
        %r = arith.addi %v, %one : i32
        affine.store %r, %a[%i, %j] : memref<5x7xi32>
      }
    }
    return
  }
}
