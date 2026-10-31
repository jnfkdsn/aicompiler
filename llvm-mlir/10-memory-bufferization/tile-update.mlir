module {
  func.func @tile_update(%m: memref<4x4xi32>) -> (i32, i32) {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c2 = arith.constant 2 : index
    %v = arith.constant 99 : i32
    %t = bufferization.to_tensor %m restrict writable : memref<4x4xi32> to tensor<4x4xi32>
    %tile = tensor.extract_slice %t[1, 1][2, 2][1, 1]
      : tensor<4x4xi32> to tensor<2x2xi32>
    %filled = linalg.fill ins(%v : i32) outs(%tile : tensor<2x2xi32>) -> tensor<2x2xi32>
    %u = tensor.insert_slice %filled into %t[1, 1][2, 2][1, 1]
      : tensor<2x2xi32> into tensor<4x4xi32>
    %inside = tensor.extract %u[%c1, %c2] : tensor<4x4xi32>
    %outside = tensor.extract %u[%c0, %c0] : tensor<4x4xi32>
    return %inside, %outside : i32, i32
  }
}
