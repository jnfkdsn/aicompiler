module {
  func.func @patch(%a: tensor<4x4xi32>) -> (tensor<2x2xi32>, tensor<4x4xi32>) {
    %roi = tensor.extract_slice %a[1, 1][2, 2][1, 1]
      : tensor<4x4xi32> to tensor<2x2xi32>
    %c0 = arith.constant 0 : index
    %v = arith.constant 99 : i32
    %changed = tensor.insert %v into %roi[%c0, %c0] : tensor<2x2xi32>
    %b = tensor.insert_slice %changed into %a[1, 1][2, 2][1, 1]
      : tensor<2x2xi32> into tensor<4x4xi32>
    return %roi, %b : tensor<2x2xi32>, tensor<4x4xi32>
  }
}
