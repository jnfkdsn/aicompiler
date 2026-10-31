module {
  func.func @storage() -> i32 {
    %c1 = arith.constant 1 : index
    %c2 = arith.constant 2 : index
    %v = arith.constant 7 : i32
    %m = memref.alloc() : memref<2x3xi32>
    memref.store %v, %m[%c1, %c2] : memref<2x3xi32>
    %r = memref.load %m[%c1, %c2] : memref<2x3xi32>
    memref.dealloc %m : memref<2x3xi32>
    return %r : i32
  }
}
