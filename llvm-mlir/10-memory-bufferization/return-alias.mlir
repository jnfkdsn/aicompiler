module {
  func.func @return_alias(%m: memref<4xi32>) -> memref<4xi32> {
    return %m : memref<4xi32>
  }
}
