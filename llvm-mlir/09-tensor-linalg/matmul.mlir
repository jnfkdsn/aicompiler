module {
  func.func @matmul(%a: tensor<2x3xf32>, %b: tensor<3x2xf32>) -> tensor<2x2xf32> {
    %zero = arith.constant 0.0 : f32
    %empty = tensor.empty() : tensor<2x2xf32>
    %init = linalg.fill ins(%zero : f32) outs(%empty : tensor<2x2xf32>) -> tensor<2x2xf32>
    %r = linalg.matmul ins(%a, %b : tensor<2x3xf32>, tensor<3x2xf32>)
                       outs(%init : tensor<2x2xf32>) -> tensor<2x2xf32>
    return %r : tensor<2x2xf32>
  }
}
