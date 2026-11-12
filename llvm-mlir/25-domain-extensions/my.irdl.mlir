module {
  irdl.dialect @my {
    irdl.operation @add {
      %i=irdl.is i32
      irdl.operands(lhs: %i,rhs: %i)
      irdl.results(result: %i)
    }
  }
}
