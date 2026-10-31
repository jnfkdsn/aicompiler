module {
  llvm.func @sum_pair(%p: !llvm.ptr) -> i32 {
    %q = llvm.getelementptr %p[1] : (!llvm.ptr) -> !llvm.ptr, i32
    %x = llvm.load %p : !llvm.ptr -> i32
    %y = llvm.load %q : !llvm.ptr -> i32
    %s = llvm.add %x, %y : i32
    llvm.return %s : i32
  }
}
