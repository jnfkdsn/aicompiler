module {
  func.func @subsample(%a: tensor<4x4xi32>) -> tensor<2x2xi32> {
    %r = tensor.extract_slice %a[0, 0][2, 2][2, 2]
      : tensor<4x4xi32> to tensor<2x2xi32>
    return %r : tensor<2x2xi32>
  }
}
