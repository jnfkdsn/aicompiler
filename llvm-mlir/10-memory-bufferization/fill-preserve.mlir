module {
  func.func @fill_preserve(%m: memref<4xi32>) -> (i32, i32) {
    %c0 = arith.constant 0 : index
    %v = arith.constant 99 : i32
    %t = bufferization.to_tensor %m restrict writable : memref<4xi32> to tensor<4xi32>
    %u = linalg.fill ins(%v : i32) outs(%t : tensor<4xi32>) -> tensor<4xi32>
    %old = tensor.extract %t[%c0] : tensor<4xi32>
    %new = tensor.extract %u[%c0] : tensor<4xi32>
    return %old, %new : i32, i32
  }
}
