module {
  func.func @bounded(%out: memref<4xindex>) {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c4 = arith.constant 4 : index
    scf.for %i = %c0 to %c4 step %c1 {
      %next = arith.addi %i, %c1 : index
      memref.store %next, %out[%i] : memref<4xindex>
    }
    return
  }
}
