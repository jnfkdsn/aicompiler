module {
  func.func @parallel(%x: memref<10xf32>, %y: memref<10xf32>) {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c3 = arith.constant 3 : index
    %c4 = arith.constant 4 : index
    %c10 = arith.constant 10 : index
    %one = arith.constant 1.0 : f32
    %two = arith.constant 2.0 : f32
    scf.parallel (%block) = (%c0) to (%c3) step (%c1) {
      scf.parallel (%t) = (%c0) to (%c4) step (%c1) {
        %base = arith.muli %block, %c4 : index
        %i = arith.addi %base, %t : index
        %valid = arith.cmpi ult, %i, %c10 : index
        scf.if %valid {
          %a = memref.load %x[%i] : memref<10xf32>
          %b = arith.addf %a, %one : f32
          %c = arith.mulf %b, %two : f32
          memref.store %c, %y[%i] : memref<10xf32>
        }
        scf.reduce
      }
      scf.reduce
    }
    return
  }
}
