module {
  func.func @reshape(%a: tensor<2x3xf32>) -> tensor<3x2xf32> {
    %flat = tensor.collapse_shape %a [[0, 1]]
      : tensor<2x3xf32> into tensor<6xf32>
    %r = tensor.expand_shape %flat [[0, 1]] output_shape [3, 2]
      : tensor<6xf32> into tensor<3x2xf32>
    return %r : tensor<3x2xf32>
  }
}
