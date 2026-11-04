module {
  func.func @crop(%src: memref<6x8xi32>, %out: memref<3x4xi32>, %row0: index, %col0: index) attributes {llvm.emit_c_interface} {
    affine.for %i = 0 to 3 {
      affine.for %j = 0 to 4 {
        %row = affine.apply affine_map<(i)[r0] -> (i + r0)>(%i)[%row0]
        %col = affine.apply affine_map<(j)[c0] -> (j + c0)>(%j)[%col0]
        %v = affine.load %src[%row, %col] : memref<6x8xi32>
        affine.store %v, %out[%i, %j] : memref<3x4xi32>
      }
    }
    return
  }
}
