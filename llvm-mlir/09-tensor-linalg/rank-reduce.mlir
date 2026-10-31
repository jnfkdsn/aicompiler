module {
  func.func @row(%a: tensor<4x4xi32>) -> tensor<4xi32> {
    %r = tensor.extract_slice %a[2, 0][1, 4][1, 1]
      : tensor<4x4xi32> to tensor<4xi32>
    return %r : tensor<4xi32>
  }
}
