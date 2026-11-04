module {
  func.func @values(%x: memref<2x4xf32>, %y: memref<4x2xf32>) attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %zero = arith.constant 0.0 : f32
    %one = arith.constant 1.0 : f32
    %tile = vector.transfer_read %x[%c0, %c0], %zero {in_bounds = [true, true]}
      : memref<2x4xf32>, vector<2x4xf32>
    %ones = vector.broadcast %one : f32 to vector<2x4xf32>
    %sum = arith.addf %tile, %ones : vector<2x4xf32>
    %t = vector.transpose %sum, [1, 0] : vector<2x4xf32> to vector<4x2xf32>
    vector.transfer_write %t, %y[%c0, %c0] {in_bounds = [true, true]}
      : vector<4x2xf32>, memref<4x2xf32>
    return
  }
  func.func @identity(%v: vector<2x4xf32>) -> vector<2x4xf32> {
    return %v : vector<2x4xf32>
  }
}
