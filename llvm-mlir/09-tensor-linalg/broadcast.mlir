module {
  func.func @bias(%a: tensor<2x3xf32>, %bias: tensor<3xf32>) -> tensor<2x3xf32> {
    %empty = tensor.empty() : tensor<2x3xf32>
    %r = linalg.generic {
      indexing_maps = [affine_map<(i, j) -> (i, j)>,
                       affine_map<(i, j) -> (j)>,
                       affine_map<(i, j) -> (i, j)>],
      iterator_types = ["parallel", "parallel"]
    } ins(%a, %bias : tensor<2x3xf32>, tensor<3xf32>)
      outs(%empty : tensor<2x3xf32>) {
    ^bb0(%x: f32, %b: f32, %unused: f32):
      %v = arith.addf %x, %b : f32
      linalg.yield %v : f32
    } -> tensor<2x3xf32>
    return %r : tensor<2x3xf32>
  }
}
