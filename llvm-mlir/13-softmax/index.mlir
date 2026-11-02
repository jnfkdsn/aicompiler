module {
  func.func @tiles(%n: index, %tile: index) -> index attributes {llvm.emit_c_interface} {
    %count = index.ceildivu %n, %tile
    return %count : index
  }
  func.func @width_sensitive() -> index attributes {llvm.emit_c_interface} {
    %large = index.constant 4294967298
    %two = index.constant 2
    %r = index.divu %large, %two
    return %r : index
  }
}
