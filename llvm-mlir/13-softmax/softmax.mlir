module {
  func.func @softmax(%x: tensor<?x?xf32>) -> tensor<?x?xf32> attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %m = tensor.dim %x, %c0 : tensor<?x?xf32>
    %n = tensor.dim %x, %c1 : tensor<?x?xf32>
    %neg_inf = arith.constant 0xFF800000 : f32
    %zero = arith.constant 0.0 : f32
    %row_empty = tensor.empty(%m) : tensor<?xf32>
    %max_init = linalg.fill ins(%neg_inf : f32) outs(%row_empty : tensor<?xf32>) -> tensor<?xf32>
    %max = linalg.generic {
      indexing_maps = [affine_map<(i,j) -> (i,j)>, affine_map<(i,j) -> (i)>],
      iterator_types = ["parallel", "reduction"]
    } ins(%x : tensor<?x?xf32>) outs(%max_init : tensor<?xf32>) {
    ^bb0(%v: f32, %acc: f32):
      %r = arith.maximumf %v, %acc : f32
      linalg.yield %r : f32
    } -> tensor<?xf32>
    %matrix_empty = tensor.empty(%m, %n) : tensor<?x?xf32>
    %exp = linalg.generic {
      indexing_maps = [affine_map<(i,j) -> (i,j)>, affine_map<(i,j) -> (i)>, affine_map<(i,j) -> (i,j)>],
      iterator_types = ["parallel", "parallel"]
    } ins(%x, %max : tensor<?x?xf32>, tensor<?xf32>) outs(%matrix_empty : tensor<?x?xf32>) {
    ^bb0(%v: f32, %row_max: f32, %unused: f32):
      %shift = arith.subf %v, %row_max : f32
      %e = math.exp %shift : f32
      linalg.yield %e : f32
    } -> tensor<?x?xf32>
    %sum_empty = tensor.empty(%m) : tensor<?xf32>
    %sum_init = linalg.fill ins(%zero : f32) outs(%sum_empty : tensor<?xf32>) -> tensor<?xf32>
    %sum = linalg.generic {
      indexing_maps = [affine_map<(i,j) -> (i,j)>, affine_map<(i,j) -> (i)>],
      iterator_types = ["parallel", "reduction"]
    } ins(%exp : tensor<?x?xf32>) outs(%sum_init : tensor<?xf32>) {
    ^bb0(%e: f32, %acc: f32):
      %r = arith.addf %acc, %e : f32
      linalg.yield %r : f32
    } -> tensor<?xf32>
    %out_empty = tensor.empty(%m, %n) : tensor<?x?xf32>
    %out = linalg.generic {
      indexing_maps = [affine_map<(i,j) -> (i,j)>, affine_map<(i,j) -> (i)>, affine_map<(i,j) -> (i,j)>],
      iterator_types = ["parallel", "parallel"]
    } ins(%exp, %sum : tensor<?x?xf32>, tensor<?xf32>) outs(%out_empty : tensor<?x?xf32>) {
    ^bb0(%e: f32, %row_sum: f32, %unused: f32):
      %p = arith.divf %e, %row_sum : f32
      linalg.yield %p : f32
    } -> tensor<?x?xf32>
    return %out : tensor<?x?xf32>
  }
}
