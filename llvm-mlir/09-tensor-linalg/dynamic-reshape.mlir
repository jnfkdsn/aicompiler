module {
  func.func @flatten_restore(%a: tensor<?x3xf32>) -> tensor<?x3xf32> {
    %c0 = arith.constant 0 : index
    %rows = tensor.dim %a, %c0 : tensor<?x3xf32>
    %flat = tensor.collapse_shape %a [[0, 1]]
      : tensor<?x3xf32> into tensor<?xf32>
    %r = tensor.expand_shape %flat [[0, 1]] output_shape [%rows, 3]
      : tensor<?xf32> into tensor<?x3xf32>
    return %r : tensor<?x3xf32>
  }
}
