#csr = #sparse_tensor.encoding<{ map=(i,j)->(i:dense,j:compressed) }>
module {
 func.func @matvec(%a:tensor<2x3xf32,#csr>,%x:tensor<3xf32>,%init:tensor<2xf32>)->tensor<2xf32>{
  %r=linalg.generic {
   indexing_maps=[affine_map<(i,j)->(i,j)>,affine_map<(i,j)->(j)>,affine_map<(i,j)->(i)>],
   iterator_types=["parallel","reduction"]
  } ins(%a,%x:tensor<2x3xf32,#csr>,tensor<3xf32>) outs(%init:tensor<2xf32>){
   ^bb0(%av:f32,%xv:f32,%acc:f32):
    %p=arith.mulf %av,%xv:f32
    %s=arith.addf %acc,%p:f32
    linalg.yield %s:f32
  }->tensor<2xf32>
  return %r:tensor<2xf32>
 }
}
