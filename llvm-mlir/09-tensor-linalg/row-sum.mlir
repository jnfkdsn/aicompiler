module {
  func.func @row_sum(%a: tensor<2x3xf32>) -> tensor<2xf32> {
    %zero = arith.constant 0.0 : f32
    %empty = tensor.empty() : tensor<2xf32>
    %init = linalg.fill ins(%zero : f32) outs(%empty : tensor<2xf32>) -> tensor<2xf32>
    %r = linalg.generic {
      indexing_maps = [affine_map<(i, j) -> (i, j)>,
                       affine_map<(i, j) -> (i)>],
      iterator_types = ["parallel", "reduction"]
    } ins(%a : tensor<2x3xf32>) outs(%init : tensor<2xf32>) {
    ^bb0(%x: f32, %acc: f32):
      %next = arith.addf %acc, %x : f32
      linalg.yield %next : f32
    } -> tensor<2xf32>
    return %r : tensor<2xf32>
  }
}
