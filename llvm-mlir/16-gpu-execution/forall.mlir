module {
  func.func @forall(%x: memref<10xf32>, %y: memref<10xf32>) {
    %c4 = arith.constant 4 : index
    %c10 = arith.constant 10 : index
    %one = arith.constant 1.0 : f32
    %two = arith.constant 2.0 : f32
    scf.forall (%block) in (3) {
      scf.forall (%t) in (4) {
        %base = arith.muli %block, %c4 : index
        %i = arith.addi %base, %t : index
        %valid = arith.cmpi ult, %i, %c10 : index
        scf.if %valid {
          %a = memref.load %x[%i] : memref<10xf32>
          %b = arith.addf %a, %one : f32
          %c = arith.mulf %b, %two : f32
          memref.store %c, %y[%i] : memref<10xf32>
        }
      } {mapping = [#gpu.thread<x>]}
    } {mapping = [#gpu.block<x>]}
    return
  }
}
