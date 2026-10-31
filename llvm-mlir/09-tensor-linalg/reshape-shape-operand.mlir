module {
  func.func @reshape_shape(%a: tensor<2x3xf32>) -> tensor<3x2xf32> {
    %shape = arith.constant dense<[3, 2]> : tensor<2xi64>
    %r = tensor.reshape %a(%shape)
      : (tensor<2x3xf32>, tensor<2xi64>) -> tensor<3x2xf32>
    return %r : tensor<3x2xf32>
  }
}
