module {
  func.func @memory(%p: memref<4xi32>, %q: memref<4xi32>) {
    %a = memref.alloc() : memref<4xi32>
    %b = memref.alloc() : memref<4xi32>
    %left = memref.subview %a[0] [2] [1] : memref<4xi32> to memref<2xi32, strided<[1]>>
    %right = memref.subview %a[2] [2] [1] : memref<4xi32> to memref<2xi32, strided<[1], offset: 2>>
    %c0 = arith.constant 0 : index
    %c7 = arith.constant 7 : i32
    memref.store %c7, %a[%c0] : memref<4xi32>
    memref.dealloc %a : memref<4xi32>
    memref.dealloc %b : memref<4xi32>
    return
  }
}
