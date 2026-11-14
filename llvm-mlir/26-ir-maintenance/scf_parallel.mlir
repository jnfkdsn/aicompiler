module {
 func.func @parallel_sum(%n:index,%init:i32)->i32 {
  %zero=arith.constant 0:index
  %one=arith.constant 1:index
  %r=scf.parallel(%i)=(%zero)to(%n)step(%one)init(%init)->i32{
   %v=arith.index_cast %i:index to i32
   scf.reduce(%v:i32){
    ^bb0(%a:i32,%b:i32):
     %s=arith.addi %a,%b:i32
     scf.reduce.return %s:i32
   }
  }
  return %r:i32
 }
 func.func @forall_value()->i32{
  %empty=tensor.empty():tensor<4xi32>
  %r=scf.forall(%i) in (4) shared_outs(%out=%empty)->(tensor<4xi32>){
   %v=arith.index_cast %i:index to i32
   %tile=tensor.from_elements %v:tensor<1xi32>
   scf.forall.in_parallel {
    tensor.parallel_insert_slice %tile into %out[%i][1][1]:tensor<1xi32> into tensor<4xi32>
   }
  }
  %zero=arith.constant 0:index
  %three=arith.constant 3:index
  %a=tensor.extract %r[%zero]:tensor<4xi32>
  %b=tensor.extract %r[%three]:tensor<4xi32>
  %s=arith.addi %a,%b:i32
  return %s:i32
 }
}
