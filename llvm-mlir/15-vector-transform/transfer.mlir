module {
  func.func @transfer(%x: memref<?xf32>, %y: memref<?xf32>) attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c4 = arith.constant 4 : index
    %zero = arith.constant 0.0 : f32
    %one = arith.constant dense<1.0> : vector<4xf32>
    %two = arith.constant dense<2.0> : vector<4xf32>
    %n = memref.dim %x, %c0 : memref<?xf32>
    scf.for %i = %c0 to %n step %c4 {
      %v = vector.transfer_read %x[%i], %zero : memref<?xf32>, vector<4xf32>
      %a = arith.addf %v, %one : vector<4xf32>
      %b = arith.mulf %a, %two : vector<4xf32>
      vector.transfer_write %b, %y[%i] : vector<4xf32>, memref<?xf32>
    }
    return
  }
}
