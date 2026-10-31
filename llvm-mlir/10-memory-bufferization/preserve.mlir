module {
  func.func @preserve(%m: memref<4xi32>) -> (i32, i32, i32) {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %v = arith.constant 99 : i32
    %t = bufferization.to_tensor %m restrict writable : memref<4xi32> to tensor<4xi32>
    %u = tensor.insert %v into %t[%c0] : tensor<4xi32>
    %old = tensor.extract %t[%c0] : tensor<4xi32>
    %new = tensor.extract %u[%c0] : tensor<4xi32>
    %unchanged = tensor.extract %u[%c1] : tensor<4xi32>
    return %old, %new, %unchanged : i32, i32, i32
  }
}
