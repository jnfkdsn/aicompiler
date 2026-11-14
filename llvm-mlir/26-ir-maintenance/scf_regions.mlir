module {
 func.func @adjust(%flag:i1,%x:i32)->i32 {
  %one=arith.constant 1:i32
  %r=scf.execute_region -> i32 {
   cf.cond_br %flag,^yes,^no
   ^yes:
    %a=arith.addi %x,%one:i32
    scf.yield %a:i32
   ^no:
    %b=arith.subi %x,%one:i32
    scf.yield %b:i32
  }
  return %r:i32
 }
 func.func @choose(%tag:index,%x:i32)->i32 {
  %r=scf.index_switch %tag -> i32
  case 0 {scf.yield %x:i32}
  case 2 {
   %twice=arith.addi %x,%x:i32
   scf.yield %twice:i32
  }
  default {
   %one=arith.constant 1:i32
   %v=arith.subi %x,%one:i32
   scf.yield %v:i32
  }
  return %r:i32
 }
}
