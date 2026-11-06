module attributes {gpu.container_module} {
  gpu.module @kernels {
    gpu.func @rotate(%x: memref<4xf32, #gpu.address_space<global>>,
                     %y: memref<4xf32, #gpu.address_space<global>>)
      workgroup(%tile: memref<4xf32, #gpu.address_space<workgroup>>)
      private(%scratch: memref<1xf32, #gpu.address_space<private>>) kernel
      attributes {known_block_size = array<i32: 4, 1, 1>, known_grid_size = array<i32: 1, 1, 1>} {
      %t = gpu.thread_id x
      %c1 = arith.constant 1 : index
      %c4 = arith.constant 4 : index
      %v = memref.load %x[%t] : memref<4xf32, #gpu.address_space<global>>
      memref.store %v, %tile[%t] : memref<4xf32, #gpu.address_space<workgroup>>
      gpu.barrier
      %next = arith.addi %t, %c1 : index
      %j = arith.remui %next, %c4 : index
      %w = memref.load %tile[%j] : memref<4xf32, #gpu.address_space<workgroup>>
      memref.store %w, %y[%t] : memref<4xf32, #gpu.address_space<global>>
      gpu.return
    }
  }
}
