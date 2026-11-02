module {
  func.func @row_softmax(%x: memref<?x?xf32>, %out: memref<?x?xf32>) attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %m = memref.dim %x, %c0 : memref<?x?xf32>
    %n = memref.dim %x, %c1 : memref<?x?xf32>
    %neg_inf = arith.constant 0xFF800000 : f32
    %zero = arith.constant 0.0 : f32
    scf.for %i = %c0 to %m step %c1 {
      %max = scf.for %j = %c0 to %n step %c1 iter_args(%acc = %neg_inf) -> f32 {
        %v = memref.load %x[%i, %j] : memref<?x?xf32>
        %next = arith.maximumf %v, %acc : f32
        scf.yield %next : f32
      }
      %sum = scf.for %j = %c0 to %n step %c1 iter_args(%acc = %zero) -> f32 {
        %v = memref.load %x[%i, %j] : memref<?x?xf32>
        %shift = arith.subf %v, %max : f32
        %e = math.exp %shift : f32
        memref.store %e, %out[%i, %j] : memref<?x?xf32>
        %next = arith.addf %acc, %e : f32
        scf.yield %next : f32
      }
      scf.for %j = %c0 to %n step %c1 {
        %e = memref.load %out[%i, %j] : memref<?x?xf32>
        %p = arith.divf %e, %sum : f32
        memref.store %p, %out[%i, %j] : memref<?x?xf32>
      }
    }
    return
  }
}
