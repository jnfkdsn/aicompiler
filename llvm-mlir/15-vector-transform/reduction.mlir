module {
  func.func @reduction(%x: memref<4xf32>) -> f32 attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %zero = arith.constant 0.0 : f32
    %v = vector.transfer_read %x[%c0], %zero {in_bounds = [true]} : memref<4xf32>, vector<4xf32>
    %sum = vector.reduction <add>, %v, %zero : vector<4xf32> into f32
    return %sum : f32
  }
  func.func @dot(%a: memref<2x3xf32>, %b: memref<3x2xf32>, %c: memref<2x2xf32>) attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %zero = arith.constant 0.0 : f32
    %av = vector.transfer_read %a[%c0, %c0], %zero {in_bounds = [true, true]} : memref<2x3xf32>, vector<2x3xf32>
    %bv = vector.transfer_read %b[%c0, %c0], %zero {in_bounds = [true, true]} : memref<3x2xf32>, vector<3x2xf32>
    %cv = vector.transfer_read %c[%c0, %c0], %zero {in_bounds = [true, true]} : memref<2x2xf32>, vector<2x2xf32>
    %r = vector.contract {
      indexing_maps = [affine_map<(i,j,k) -> (i,k)>, affine_map<(i,j,k) -> (k,j)>, affine_map<(i,j,k) -> (i,j)>],
      iterator_types = ["parallel", "parallel", "reduction"]}
      %av, %bv, %cv : vector<2x3xf32>, vector<3x2xf32> into vector<2x2xf32>
    vector.transfer_write %r, %c[%c0, %c0] {in_bounds = [true, true]} : vector<2x2xf32>, memref<2x2xf32>
    return
  }
}
