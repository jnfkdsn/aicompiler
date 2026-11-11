module {
  func.func @reuse(%buffer: memref<4xf32>) -> f32 attributes {llvm.emit_c_interface} {
    %t = bufferization.to_tensor %buffer restrict writable : memref<4xf32> to tensor<4xf32>
    %r = my.add_one %t outs(%t) : tensor<4xf32>
    %c0 = arith.constant 0 : index
    %new = tensor.extract %r[%c0] : tensor<4xf32>
    return %new : f32
  }
  func.func @preserve(%buffer: memref<4xf32>) -> (f32, f32) attributes {llvm.emit_c_interface} {
    %t = bufferization.to_tensor %buffer restrict writable : memref<4xf32> to tensor<4xf32>
    %r = my.add_one %t outs(%t) : tensor<4xf32>
    %c0 = arith.constant 0 : index
    %old = tensor.extract %t[%c0] : tensor<4xf32>
    %new = tensor.extract %r[%c0] : tensor<4xf32>
    return %old, %new : f32, f32
  }
}
