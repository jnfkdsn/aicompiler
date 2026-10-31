module {
  func.func @cast_view(%m: memref<4x4xi32>) -> i32 {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %w = memref.subview %m[1, 1][2, 2][1, 1]
      : memref<4x4xi32> to memref<2x2xi32, strided<[4, 1], offset: 5>>
    %d = memref.cast %w : memref<2x2xi32, strided<[4, 1], offset: 5>>
      to memref<?x?xi32, strided<[?, ?], offset: ?>>
    %r = memref.load %d[%c0, %c1] : memref<?x?xi32, strided<[?, ?], offset: ?>>
    return %r : i32
  }
}
