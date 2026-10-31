module {
  func.func @readonly(%m: memref<4xi32>) -> i32 {
    %c0 = arith.constant 0 : index
    %v = arith.constant 99 : i32
    %t = bufferization.to_tensor %m restrict : memref<4xi32> to tensor<4xi32>
    %u = tensor.insert %v into %t[%c0] : tensor<4xi32>
    %new = tensor.extract %u[%c0] : tensor<4xi32>
    return %new : i32
  }
}
