module {
  func.func @elementwise(%x: tensor<?x?xi32>) -> tensor<?x?xi32> attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %m = tensor.dim %x, %c0 : tensor<?x?xi32>
    %n = tensor.dim %x, %c1 : tensor<?x?xi32>
    %init = tensor.empty(%m, %n) : tensor<?x?xi32>
    %p = linalg.generic {
      indexing_maps = [affine_map<(i,j) -> (i,j)>, affine_map<(i,j) -> (i,j)>],
      iterator_types = ["parallel", "parallel"]
    } ins(%x : tensor<?x?xi32>) outs(%init : tensor<?x?xi32>) {
    ^bb0(%v: i32, %unused: i32):
      %one = arith.constant 1 : i32
      %r = arith.addi %v, %one : i32
      linalg.yield %r : i32
    } -> tensor<?x?xi32>
    %out_init = tensor.empty(%m, %n) : tensor<?x?xi32>
    %y = linalg.generic {
      indexing_maps = [affine_map<(i,j) -> (i,j)>, affine_map<(i,j) -> (i,j)>],
      iterator_types = ["parallel", "parallel"]
    } ins(%p : tensor<?x?xi32>) outs(%out_init : tensor<?x?xi32>) {
    ^bb0(%v: i32, %unused: i32):
      %two = arith.constant 2 : i32
      %r = arith.muli %v, %two : i32
      linalg.yield %r : i32
    } -> tensor<?x?xi32>
    return %y : tensor<?x?xi32>
  }
}
