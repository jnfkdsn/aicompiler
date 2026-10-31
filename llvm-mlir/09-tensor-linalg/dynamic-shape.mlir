module {
  func.func @shape(%a: tensor<?x3xf32>) -> (index, index) {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %rows = tensor.dim %a, %c0 : tensor<?x3xf32>
    %cols = tensor.dim %a, %c1 : tensor<?x3xf32>
    return %rows, %cols : index, index
  }
}
