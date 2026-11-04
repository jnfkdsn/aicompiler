module {
  func.func @split(%x: memref<?xf32>, %y: memref<?xf32>) attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c4 = arith.constant 4 : index
    %one = arith.constant 1.0 : f32
    %two = arith.constant 2.0 : f32
    %ones = arith.constant dense<1.0> : vector<4xf32>
    %twos = arith.constant dense<2.0> : vector<4xf32>
    %n = memref.dim %x, %c0 : memref<?xf32>
    %rest = arith.remui %n, %c4 : index
    %end = arith.subi %n, %rest : index
    scf.for %i = %c0 to %end step %c4 {
      %v = vector.load %x[%i] : memref<?xf32>, vector<4xf32>
      %a = arith.addf %v, %ones : vector<4xf32>
      %b = arith.mulf %a, %twos : vector<4xf32>
      vector.store %b, %y[%i] : memref<?xf32>, vector<4xf32>
    }
    scf.for %i = %end to %n step %c1 {
      %v = memref.load %x[%i] : memref<?xf32>
      %a = arith.addf %v, %one : f32
      %b = arith.mulf %a, %two : f32
      memref.store %b, %y[%i] : memref<?xf32>
    }
    return
  }
}
