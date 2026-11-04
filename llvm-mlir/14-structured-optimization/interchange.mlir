module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(%root: !transform.any_op {transform.readonly}) {
    %ops = transform.structured.match ops{["linalg.generic"]} in %root : (!transform.any_op) -> !transform.any_op
    %changed = transform.structured.interchange %ops iterator_interchange = [1, 0]
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }
}
