module {
  func.func @coordinates(%rows: index) -> tensor<?x3xindex> {
    %c10 = arith.constant 10 : index
    %t = tensor.generate %rows {
    ^bb0(%i: index, %j: index):
      %base = arith.muli %i, %c10 : index
      %v = arith.addi %base, %j : index
      tensor.yield %v : index
    } : tensor<?x3xindex>
    return %t : tensor<?x3xindex>
  }
}
