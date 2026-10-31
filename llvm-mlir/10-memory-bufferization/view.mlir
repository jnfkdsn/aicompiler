module {
  func.func @window(%m: memref<4x4xi32>) -> (i32, index, index, index) {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c2 = arith.constant 2 : index
    %v = arith.constant 99 : i32
    %w = memref.subview %m[1, 1][2, 2][1, 1]
      : memref<4x4xi32> to memref<2x2xi32, strided<[4, 1], offset: 5>>
    memref.store %v, %w[%c0, %c1]
      : memref<2x2xi32, strided<[4, 1], offset: 5>>
    %r = memref.load %m[%c1, %c2] : memref<4x4xi32>
    %base, %offset, %sizes:2, %strides:2 = memref.extract_strided_metadata %w
      : memref<2x2xi32, strided<[4, 1], offset: 5>> -> memref<i32>, index, index, index, index, index
    return %r, %offset, %strides#0, %strides#1 : i32, index, index, index
  }
}
