module {
  func.func @update(%a: tensor<2x3xf32>, %value: f32) -> (f32, f32, tensor<2x3xf32>) {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %b = tensor.insert %value into %a[%c0, %c1] : tensor<2x3xf32>
    %old = tensor.extract %a[%c0, %c1] : tensor<2x3xf32>
    %new = tensor.extract %b[%c0, %c1] : tensor<2x3xf32>
    return %old, %new, %b : f32, f32, tensor<2x3xf32>
  }
}
