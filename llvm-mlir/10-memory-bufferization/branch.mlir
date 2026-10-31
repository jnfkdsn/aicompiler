module {
  func.func @choose(%m: memref<4xi32>, %useFresh: i1) -> i32 {
    %c0 = arith.constant 0 : index
    %v = arith.constant 77 : i32
    %selected = scf.if %useFresh -> memref<4xi32> {
      %fresh = memref.alloc() : memref<4xi32>
      memref.store %v, %fresh[%c0] : memref<4xi32>
      scf.yield %fresh : memref<4xi32>
    } else {
      scf.yield %m : memref<4xi32>
    }
    %r = memref.load %selected[%c0] : memref<4xi32>
    return %r : i32
  }
}
