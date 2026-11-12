module {
 func.func @add(%a:tensor<2x3xf32>,%b:tensor<2x3xf32>)->tensor<2x3xf32>{
  %r=tosa.add %a,%b:(tensor<2x3xf32>,tensor<2x3xf32>)->tensor<2x3xf32>
  return %r:tensor<2x3xf32>
 }
}
