module {
  func.func @advance(%i: index) -> index {
    %one = arith.constant 1 : index
    %next = arith.addi %i, %one : index
    return %next : index
  }
}
