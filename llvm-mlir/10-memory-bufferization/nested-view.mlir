module {
  func.func @nested(%m: memref<4x4xi32>) -> (i32, i32) {
    %c0 = arith.constant 0 : index
    %w = memref.subview %m[1, 1][2, 2][1, 1]
      : memref<4x4xi32> to memref<2x2xi32, strided<[4, 1], offset: 5>>
    %s = memref.subview %w[1, 0][1, 2][1, 1]
      : memref<2x2xi32, strided<[4, 1], offset: 5>>
        to memref<1x2xi32, strided<[4, 1], offset: 9>>
    %step = memref.subview %m[0, 0][2, 2][2, 2]
      : memref<4x4xi32> to memref<2x2xi32, strided<[8, 2]>>
    %c1 = arith.constant 1 : index
    %a = memref.load %s[%c0, %c0] : memref<1x2xi32, strided<[4, 1], offset: 9>>
    %b = memref.load %step[%c1, %c1] : memref<2x2xi32, strided<[8, 2]>>
    return %a, %b : i32, i32
  }
}
