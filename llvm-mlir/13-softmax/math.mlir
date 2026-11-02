module {
  func.func @exp_value(%x: f32) -> f32 attributes {llvm.emit_c_interface} {
    %r = math.exp %x : f32
    return %r : f32
  }
  func.func @exp_minus_one(%x: f32) -> f32 attributes {llvm.emit_c_interface} {
    %one = arith.constant 1.0 : f32
    %e = math.exp %x : f32
    %r = arith.subf %e, %one : f32
    return %r : f32
  }
  func.func @accurate_small_exp(%x: f32) -> f32 attributes {llvm.emit_c_interface} {
    %r = math.expm1 %x : f32
    return %r : f32
  }
}
