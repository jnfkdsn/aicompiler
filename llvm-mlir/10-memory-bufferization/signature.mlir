module {
  func.func @updated(%t: tensor<4xi32>) -> tensor<4xi32> {
    %c0 = arith.constant 0 : index
    %v = arith.constant 99 : i32
    %u = tensor.insert %v into %t[%c0] : tensor<4xi32>
    return %u : tensor<4xi32>
  }
}
