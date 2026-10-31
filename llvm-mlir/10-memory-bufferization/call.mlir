module {
  func.func @make() -> memref<4xi32> {
    %c0 = arith.constant 0 : index
    %v = arith.constant 42 : i32
    %m = memref.alloc() : memref<4xi32>
    memref.store %v, %m[%c0] : memref<4xi32>
    return %m : memref<4xi32>
  }
  func.func @consume() -> i32 {
    %c0 = arith.constant 0 : index
    %m = func.call @make() : () -> memref<4xi32>
    %v = memref.load %m[%c0] : memref<4xi32>
    return %v : i32
  }
}
