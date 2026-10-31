module {
  func.func @add_dynamic(%a: tensor<?x3xf32>, %b: tensor<?x3xf32>) -> tensor<?x3xf32> {
    %c0 = arith.constant 0 : index
    %m = tensor.dim %a, %c0 : tensor<?x3xf32>
    %n = tensor.dim %b, %c0 : tensor<?x3xf32>
    %same = arith.cmpi eq, %m, %n : index
    cf.assert %same, "row counts must match"
    %empty = tensor.empty(%m) : tensor<?x3xf32>
    %r = linalg.generic {
      indexing_maps = [affine_map<(i, j) -> (i, j)>,
                       affine_map<(i, j) -> (i, j)>,
                       affine_map<(i, j) -> (i, j)>],
      iterator_types = ["parallel", "parallel"]
    } ins(%a, %b : tensor<?x3xf32>, tensor<?x3xf32>)
      outs(%empty : tensor<?x3xf32>) {
    ^bb0(%x: f32, %y: f32, %unused: f32):
      %sum = arith.addf %x, %y : f32
      linalg.yield %sum : f32
    } -> tensor<?x3xf32>
    return %r : tensor<?x3xf32>
  }
}
