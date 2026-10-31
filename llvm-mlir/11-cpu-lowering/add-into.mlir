module {
  func.func @add_into(
      %a: memref<?x?xf32, strided<[?, ?], offset: ?>>,
      %b: memref<?x?xf32, strided<[?, ?], offset: ?>>,
      %out: memref<?x?xf32, strided<[?, ?], offset: ?>>)
      attributes {llvm.emit_c_interface} {
    linalg.generic {
      indexing_maps = [affine_map<(i, j) -> (i, j)>,
                       affine_map<(i, j) -> (i, j)>,
                       affine_map<(i, j) -> (i, j)>],
      iterator_types = ["parallel", "parallel"]
    } ins(%a, %b : memref<?x?xf32, strided<[?, ?], offset: ?>>,
                   memref<?x?xf32, strided<[?, ?], offset: ?>>)
      outs(%out : memref<?x?xf32, strided<[?, ?], offset: ?>>) {
    ^bb0(%x: f32, %y: f32, %unused: f32):
      %sum = arith.addf %x, %y : f32
      linalg.yield %sum : f32
    }
    return
  }
}
