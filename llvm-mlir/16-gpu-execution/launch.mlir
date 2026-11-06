module {
  func.func @launch(%x: memref<10xf32>, %y: memref<10xf32>) {
    %c1 = arith.constant 1 : index
    %c3 = arith.constant 3 : index
    %c4 = arith.constant 4 : index
    %c10 = arith.constant 10 : index
    %one = arith.constant 1.0 : f32
    %two = arith.constant 2.0 : f32
    gpu.launch blocks(%bx, %by, %bz) in (%gx = %c3, %gy = %c1, %gz = %c1)
      threads(%tx, %ty, %tz) in (%dx = %c4, %dy = %c1, %dz = %c1) {
      %base = arith.muli %bx, %dx : index
      %i = arith.addi %base, %tx : index
      %valid = arith.cmpi ult, %i, %c10 : index
      scf.if %valid {
        %a = memref.load %x[%i] : memref<10xf32>
        %b = arith.addf %a, %one : f32
        %c = arith.mulf %b, %two : f32
        memref.store %c, %y[%i] : memref<10xf32>
      }
      gpu.terminator
    }
    return
  }
}
