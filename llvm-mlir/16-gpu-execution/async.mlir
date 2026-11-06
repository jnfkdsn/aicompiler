module {
  func.func @run(%host_x: memref<?xf32>, %host_y: memref<?xf32>) {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c4 = arith.constant 4 : index
    %one = arith.constant 1.0 : f32
    %two = arith.constant 2.0 : f32
    %n = memref.dim %host_x, %c0 : memref<?xf32>
    %nonempty = arith.cmpi ugt, %n, %c0 : index
    scf.if %nonempty {
      %unranked_x = memref.cast %host_x : memref<?xf32> to memref<*xf32>
      %unranked_y = memref.cast %host_y : memref<?xf32> to memref<*xf32>
      gpu.host_register %unranked_x : memref<*xf32>
      gpu.host_register %unranked_y : memref<*xf32>
      %blocks = arith.ceildivui %n, %c4 : index
      %start = gpu.wait async
      %dx, %allocated_x = gpu.alloc async [%start] (%n) : memref<?xf32>
      %dy, %allocated_y = gpu.alloc async [%allocated_x] (%n) : memref<?xf32>
      %copied_in = gpu.memcpy async [%allocated_y] %dx, %host_x : memref<?xf32>, memref<?xf32>
      %computed = gpu.launch async [%copied_in]
        blocks(%bx, %by, %bz) in (%gx = %blocks, %gy = %c1, %gz = %c1)
        threads(%tx, %ty, %tz) in (%sx = %c4, %sy = %c1, %sz = %c1) {
        %base = arith.muli %bx, %sx : index
        %i = arith.addi %base, %tx : index
        %valid = arith.cmpi ult, %i, %n : index
        scf.if %valid {
          %a = memref.load %dx[%i] : memref<?xf32>
          %b = arith.addf %a, %one : f32
          %c = arith.mulf %b, %two : f32
          memref.store %c, %dy[%i] : memref<?xf32>
        }
        gpu.terminator
      }
      %copied_out = gpu.memcpy async [%computed] %host_y, %dy : memref<?xf32>, memref<?xf32>
      %freed_x = gpu.dealloc async [%copied_out] %dx : memref<?xf32>
      %freed_y = gpu.dealloc async [%freed_x] %dy : memref<?xf32>
      gpu.wait [%freed_y]
      gpu.host_unregister %unranked_x : memref<*xf32>
      gpu.host_unregister %unranked_y : memref<*xf32>
    }
    return
  }
}
