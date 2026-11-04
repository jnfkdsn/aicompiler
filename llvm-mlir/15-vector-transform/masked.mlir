module {
  func.func @masked(%x: memref<?xf32>, %y: memref<?xf32>) attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c4 = arith.constant 4 : index
    %zero = arith.constant dense<0.0> : vector<4xf32>
    %one = arith.constant dense<1.0> : vector<4xf32>
    %two = arith.constant dense<2.0> : vector<4xf32>
    %n = memref.dim %x, %c0 : memref<?xf32>
    scf.for %i = %c0 to %n step %c4 {
      %left = arith.subi %n, %i : index
      %mask = vector.create_mask %left : vector<4xi1>
      %v = vector.maskedload %x[%i], %mask, %zero : memref<?xf32>, vector<4xi1>, vector<4xf32> into vector<4xf32>
      %a = arith.addf %v, %one : vector<4xf32>
      %b = arith.mulf %a, %two : vector<4xf32>
      vector.maskedstore %y[%i], %mask, %b : memref<?xf32>, vector<4xi1>, vector<4xf32>
    }
    return
  }
}
