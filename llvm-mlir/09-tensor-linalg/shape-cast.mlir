module {
  func.func @forget_rows(%a: tensor<2x3xf32>) -> tensor<?x3xf32> {
    %r = tensor.cast %a : tensor<2x3xf32> to tensor<?x3xf32>
    return %r : tensor<?x3xf32>
  }
}
