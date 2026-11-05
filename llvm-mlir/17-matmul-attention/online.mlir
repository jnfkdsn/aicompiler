module {
  // Sequential CPU model of blocked online attention, tile size 3.
  // It validates the recurrence, not a FlashAttention GPU implementation.
  func.func @online(%q: memref<?x?xf32>, %k: memref<?x?xf32>,
      %v: memref<?x?xf32>, %out: memref<?x?xf32>,
      %lengths: memref<?xindex>, %scale: f32) attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c3 = arith.constant 3 : index
    %zero = arith.constant 0.0 : f32
    %neg_inf = arith.constant 0xFF800000 : f32
    %m = memref.dim %q, %c0 : memref<?x?xf32>
    %d = memref.dim %q, %c1 : memref<?x?xf32>
    %p = memref.dim %v, %c1 : memref<?x?xf32>
    %scores = memref.alloc() : memref<3xf32>
    scf.for %i = %c0 to %m step %c1 {
      %limit = memref.load %lengths[%i] : memref<?xindex>
      scf.for %col = %c0 to %p step %c1 {
        memref.store %zero, %out[%i, %col] : memref<?x?xf32>
      }
      %state:2 = scf.for %base = %c0 to %limit step %c3
          iter_args(%oldmax = %neg_inf, %oldsum = %zero) -> (f32, f32) {
        %left = arith.subi %limit, %base : index
        %size = arith.minui %left, %c3 : index
        %newmax = scf.for %t = %c0 to %size step %c1 iter_args(%max = %oldmax) -> f32 {
          %j = arith.addi %base, %t : index
          %dot = scf.for %h = %c0 to %d step %c1 iter_args(%acc = %zero) -> f32 {
            %a = memref.load %q[%i, %h] : memref<?x?xf32>
            %b = memref.load %k[%j, %h] : memref<?x?xf32>
            %mul = arith.mulf %a, %b : f32
            %sum = arith.addf %acc, %mul : f32
            scf.yield %sum : f32
          }
          %score = arith.mulf %dot, %scale : f32
          memref.store %score, %scores[%t] : memref<3xf32>
          %nextmax = arith.maximumf %max, %score : f32
          scf.yield %nextmax : f32
        }
        %delta = arith.subf %oldmax, %newmax : f32
        %alpha = math.exp %delta : f32
        %rescaled_sum = arith.mulf %alpha, %oldsum : f32
        %newsum = scf.for %t = %c0 to %size step %c1 iter_args(%sum = %rescaled_sum) -> f32 {
          %score = memref.load %scores[%t] : memref<3xf32>
          %shifted = arith.subf %score, %newmax : f32
          %weight = math.exp %shifted : f32
          memref.store %weight, %scores[%t] : memref<3xf32>
          %next = arith.addf %sum, %weight : f32
          scf.yield %next : f32
        }
        scf.for %col = %c0 to %p step %c1 {
          %old = memref.load %out[%i, %col] : memref<?x?xf32>
          %rescaled = arith.mulf %alpha, %old : f32
          %new = scf.for %t = %c0 to %size step %c1 iter_args(%acc = %rescaled) -> f32 {
            %j = arith.addi %base, %t : index
            %weight = memref.load %scores[%t] : memref<3xf32>
            %value = memref.load %v[%j, %col] : memref<?x?xf32>
            %mul = arith.mulf %weight, %value : f32
            %next = arith.addf %acc, %mul : f32
            scf.yield %next : f32
          }
          memref.store %new, %out[%i, %col] : memref<?x?xf32>
        }
        scf.yield %newmax, %newsum : f32, f32
      }
      %has_keys = arith.cmpi ugt, %limit, %c0 : index
      scf.if %has_keys {
        scf.for %col = %c0 to %p step %c1 {
          %weighted = memref.load %out[%i, %col] : memref<?x?xf32>
          %normalized = arith.divf %weighted, %state#1 : f32
          memref.store %normalized, %out[%i, %col] : memref<?x?xf32>
        }
      }
    }
    memref.dealloc %scores : memref<3xf32>
    return
  }
}
