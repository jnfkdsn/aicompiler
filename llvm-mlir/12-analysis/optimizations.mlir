module {
  func.func @pure(%x: i32) -> i32 {
    %c1 = arith.constant 1 : i32
    %a = arith.addi %x, %c1 : i32
    %b = arith.addi %x, %c1 : i32
    %dead = arith.muli %x, %x : i32
    %r = arith.addi %a, %b : i32
    return %r : i32
  }
  func.func @load_pair(%p: memref<1xi32>) -> i32 {
    %c0 = arith.constant 0 : index
    %a = memref.load %p[%c0] : memref<1xi32>
    %b = memref.load %p[%c0] : memref<1xi32>
    %r = arith.addi %a, %b : i32
    return %r : i32
  }
  func.func @load_store(%p: memref<1xi32>, %q: memref<1xi32>, %v: i32) -> i32 {
    %c0 = arith.constant 0 : index
    %a = memref.load %p[%c0] : memref<1xi32>
    memref.store %v, %q[%c0] : memref<1xi32>
    %b = memref.load %p[%c0] : memref<1xi32>
    %r = arith.addi %a, %b : i32
    return %r : i32
  }
  func.func @hoist(%n: index, %x: i32) -> i32 {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %one = arith.constant 1 : i32
    %zero = arith.constant 0 : i32
    %result = scf.for %i = %c0 to %n step %c1 iter_args(%acc = %zero) -> i32 {
      %scale = arith.addi %x, %one : i32
      %next = arith.addi %acc, %scale : i32
      scf.yield %next : i32
    }
    return %result : i32
  }
  func.func @do_not_hoist_div(%n: index, %x: i32, %d: i32) -> i32 {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %zero = arith.constant 0 : i32
    %result = scf.for %i = %c0 to %n step %c1 iter_args(%acc = %zero) -> i32 {
      %q = arith.divsi %x, %d : i32
      %next = arith.addi %acc, %q : i32
      scf.yield %next : i32
    }
    return %result : i32
  }
}
