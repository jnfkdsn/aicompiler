module {
 func.func @broadcast()->tensor<2xindex>{
  %a=shape.const_shape [2,1]:tensor<2xindex>
  %b=shape.const_shape [3]:tensor<1xindex>
  %r=shape.broadcast %a,%b:tensor<2xindex>,tensor<1xindex>->tensor<2xindex>
  return %r:tensor<2xindex>
 }
 func.func @compatible()->!shape.witness{
  %a=shape.const_shape [2,1]:tensor<2xindex>
  %b=shape.const_shape [3]:tensor<1xindex>
  %w=shape.cstr_broadcastable %a,%b:tensor<2xindex>,tensor<1xindex>
  return %w:!shape.witness
 }
 func.func @dynamic(%a:tensor<?x?xf32>,%b:tensor<?xf32>)->tensor<?xindex>{
  %as=shape.shape_of %a:tensor<?x?xf32>->tensor<2xindex>
  %bs=shape.shape_of %b:tensor<?xf32>->tensor<1xindex>
  %w=shape.cstr_broadcastable %as,%bs:tensor<2xindex>,tensor<1xindex>
  %r=shape.assuming %w -> (tensor<?xindex>) {
   %s=shape.broadcast %as,%bs:tensor<2xindex>,tensor<1xindex>->tensor<?xindex>
   shape.assuming_yield %s:tensor<?xindex>
  }
  return %r:tensor<?xindex>
 }
}
