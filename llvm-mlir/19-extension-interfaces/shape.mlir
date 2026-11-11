module {
  func.func @shape(%input: tensor<?xf32>, %init: tensor<?xf32>) -> index {
    %r = my.add_one %input outs(%init) : tensor<?xf32>
    %c0 = arith.constant 0 : index
    %dim = tensor.dim %r, %c0 : tensor<?xf32>
    return %dim : index
  }
  func.func @static_shape(%input: tensor<4xf32>) -> index {
    %r = my.add_one %input outs(%input) : tensor<4xf32>
    %c0 = arith.constant 0 : index
    %dim = tensor.dim %r, %c0 : tensor<4xf32>
    return %dim : index
  }
}
