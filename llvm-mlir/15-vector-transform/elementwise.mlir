#id = affine_map<(i) -> (i)>
module {
  func.func @elementwise(%x: memref<?xf32>, %y: memref<?xf32>) attributes {llvm.emit_c_interface} {
    %one = arith.constant 1.0 : f32
    %two = arith.constant 2.0 : f32
    linalg.generic {indexing_maps = [#id, #id], iterator_types = ["parallel"]}
      ins(%x : memref<?xf32>) outs(%y : memref<?xf32>) {
    ^bb0(%a: f32, %old: f32):
      %b = arith.addf %a, %one : f32
      %c = arith.mulf %b, %two : f32
      linalg.yield %c : f32
    }
    return
  }
}
