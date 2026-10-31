module {
  func.func @dynamic(%n: index) -> index {
    %m = memref.alloc(%n) : memref<?x3xi32>
    %c0 = arith.constant 0 : index
    %rows = memref.dim %m, %c0 : memref<?x3xi32>
    memref.dealloc %m : memref<?x3xi32>
    return %rows : index
  }
}
