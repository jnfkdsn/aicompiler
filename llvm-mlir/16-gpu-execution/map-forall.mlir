module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(%root: !transform.any_op {transform.readonly}) {
    %func = transform.structured.match ops{["func.func"]} in %root : (!transform.any_op) -> !transform.any_op
    %launch = transform.gpu.map_forall_to_blocks %func generate_gpu_launch : (!transform.any_op) -> !transform.any_op
    %mapped = transform.gpu.map_nested_forall_to_threads %launch block_dims = [4, 1, 1]
      sync_after_distribute = false : (!transform.any_op) -> !transform.any_op
    transform.yield
  }
}
