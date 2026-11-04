module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(%root: !transform.any_op {transform.readonly}) {
    %target = transform.structured.match ops{["linalg.generic"]} in %root
      : (!transform.any_op) -> !transform.any_op
    %tiled, %loop = transform.structured.tile_using_for %target tile_sizes [4]
      : (!transform.any_op) -> (!transform.any_op, !transform.any_op)
    transform.structured.vectorize %tiled vector_sizes [4] : !transform.any_op
    transform.yield
  }
}
