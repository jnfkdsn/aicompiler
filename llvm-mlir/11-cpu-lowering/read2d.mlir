module {
  func.func @read2d(%m: memref<?x?xi32, strided<[?, ?], offset: ?>>,
                    %i: index, %j: index) -> i32 attributes {llvm.emit_c_interface} {
    %v = memref.load %m[%i, %j] : memref<?x?xi32, strided<[?, ?], offset: ?>>
    return %v : i32
  }
}
