builtin.module {
    func.func @sum_positive(%input: memref<?xi32>) -> (i32, i32) {
        %zero_i = arith.constant 0 : index
        %one_i = arith.constant 1 : index
        %zero = arith.constant 0 : i32
        %one = arith.constant 1 :i32
        %n = memref.dim %input, %zero_i : memref<?xi32>
        %sum, %num = scf.for %i = %zero_i to %n step %one_i
            iter_args(%acc = %zero, %ncc = %zero) -> (i32, i32) {
          %x = memref.load %input[%i] : memref<?xi32>
          %positive = arith.cmpi sgt, %x, %zero : i32
          %nexts, %nextn = scf.if %positive -> (i32, i32) {
            %added = arith.addi %acc, %x : i32
            %numed = arith.addi %ncc, %one : i32
            scf.yield %added, %numed : i32, i32
          } else {
            scf.yield %acc, %ncc : i32, i32
          }
          scf.yield %nexts, %nextn : i32, i32
        }
        return %sum, %num : i32, i32
    }
}