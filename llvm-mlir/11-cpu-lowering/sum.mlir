module {
  func.func @sum(%m: memref<4xi32>) -> i32 attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c4 = arith.constant 4 : index
    %zero = arith.constant 0 : i32
    %r = scf.for %i = %c0 to %c4 step %c1 iter_args(%acc = %zero) -> i32 {
      %v = memref.load %m[%i] : memref<4xi32>
      %next = arith.addi %acc, %v : i32
      scf.yield %next : i32
    }
    return %r : i32
  }
}
