module {
  func.func @affine_add(%src: memref<5x7xi32>, %out: memref<5x7xi32>) attributes {llvm.emit_c_interface} {
    %one = arith.constant 1 : i32
    affine.for %i = 0 to 5 {
      affine.for %j = 0 to 7 {
        %v = affine.load %src[%i, %j] : memref<5x7xi32>
        %r = arith.addi %v, %one : i32
        affine.store %r, %out[%i, %j] : memref<5x7xi32>
      }
    }
    return
  }
}
