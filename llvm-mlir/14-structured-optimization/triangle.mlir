#lower = affine_set<(i,j) : (i-j >= 0)>
module {
  func.func @triangle(%out: memref<4x4xi32>) attributes {llvm.emit_c_interface} {
    %one = arith.constant 1 : i32
    %zero = arith.constant 0 : i32
    affine.for %i = 0 to 4 {
      affine.for %j = 0 to 4 {
        affine.if #lower(%i, %j) {
          affine.store %one, %out[%i, %j] : memref<4x4xi32>
        } else {
          affine.store %zero, %out[%i, %j] : memref<4x4xi32>
        }
      }
    }
    return
  }
}
