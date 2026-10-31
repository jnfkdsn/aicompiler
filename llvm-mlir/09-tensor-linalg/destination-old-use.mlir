module {
  func.func @add_preserve(%a: tensor<2x3xf32>, %b: tensor<2x3xf32>)
      -> (tensor<2x3xf32>, tensor<2x3xf32>) {
    %r = linalg.generic {
      indexing_maps = [affine_map<(i, j) -> (i, j)>,
                       affine_map<(i, j) -> (i, j)>,
                       affine_map<(i, j) -> (i, j)>],
      iterator_types = ["parallel", "parallel"]
    } ins(%a, %b : tensor<2x3xf32>, tensor<2x3xf32>)
      outs(%a : tensor<2x3xf32>) {
    ^bb0(%x: f32, %y: f32, %unused: f32):
      %sum = arith.addf %x, %y : f32
      linalg.yield %sum : f32
    } -> tensor<2x3xf32>
    return %a, %r : tensor<2x3xf32>, tensor<2x3xf32>
  }
}
