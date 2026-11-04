module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(%root: !transform.any_op {transform.readonly}) {
    transform.sequence %root : !transform.any_op failures(suppress) {
    ^bb0(%scope: !transform.any_op):
      %target = transform.structured.match ops{["linalg.generic"]} in %scope
        : (!transform.any_op) -> !transform.any_op
      %tiled, %loop = transform.structured.tile_using_for %target tile_sizes [4]
        : (!transform.any_op) -> (!transform.any_op, !transform.any_op)
      // An scf.for is not a Linalg op: fail after tiling has already happened.
      transform.structured.vectorize %loop : !transform.any_op
      transform.print %scope {name = "after suppressed failure"} : !transform.any_op
      transform.yield
    }
    transform.yield
  }
}
