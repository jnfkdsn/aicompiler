module {
  func.func @make_copy(%src: memref<2x3xf32>) -> memref<2x3xf32>
      attributes {llvm.emit_c_interface} {
    %out = memref.alloc() : memref<2x3xf32>
    memref.copy %src, %out : memref<2x3xf32> to memref<2x3xf32>
    return %out : memref<2x3xf32>
  }
}
