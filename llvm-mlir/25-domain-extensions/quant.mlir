!q = !quant.uniform<u8:f32, 0.25:128>
module {
 func.func @quantize(%x:tensor<4xf32>)->tensor<4x!q>{
  %r=quant.qcast %x:tensor<4xf32> to tensor<4x!q>
  return %r:tensor<4x!q>
 }
 func.func @dequantize(%x:tensor<4x!q>)->tensor<4xf32>{
  %r=quant.dcast %x:tensor<4x!q> to tensor<4xf32>
  return %r:tensor<4xf32>
 }
 func.func @storage(%x:tensor<4x!q>)->tensor<4xi8>{
  %r=quant.scast %x:tensor<4x!q> to tensor<4xi8>
  return %r:tensor<4xi8>
 }
}
