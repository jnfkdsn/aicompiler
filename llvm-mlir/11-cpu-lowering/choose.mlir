module {
  llvm.func @choose(%cond: i1, %a: i32, %b: i32) -> i32 {
    llvm.cond_br %cond, ^left, ^right
  ^left:
    llvm.br ^join(%a : i32)
  ^right:
    llvm.br ^join(%b : i32)
  ^join(%x: i32):
    llvm.return %x : i32
  }
}
