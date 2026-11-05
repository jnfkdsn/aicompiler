module {
  // Valid keys form the prefix [0, lengths[i]); an empty row returns zeros.
  // All matrix shapes agree, inputs and output do not overlap, scores are finite.
  func.func @attention(%q: memref<?x?xf32>, %k: memref<?x?xf32>,
      %v: memref<?x?xf32>, %out: memref<?x?xf32>,
      %lengths: memref<?xindex>, %scale: f32) attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %zero = arith.constant 0.0 : f32
    %neg_inf = arith.constant 0xFF800000 : f32
    %m = memref.dim %q, %c0 : memref<?x?xf32>
    %n = memref.dim %k, %c0 : memref<?x?xf32>
    %d = memref.dim %q, %c1 : memref<?x?xf32>
    %p = memref.dim %v, %c1 : memref<?x?xf32>
    %scores = memref.alloc(%m, %n) : memref<?x?xf32>
    scf.for %i = %c0 to %m step %c1 {
      %limit = memref.load %lengths[%i] : memref<?xindex>
      %max = scf.for %j = %c0 to %limit step %c1 iter_args(%oldmax = %neg_inf) -> f32 {
        %dot = scf.for %h = %c0 to %d step %c1 iter_args(%acc = %zero) -> f32 {
          %a = memref.load %q[%i, %h] : memref<?x?xf32>
          %b = memref.load %k[%j, %h] : memref<?x?xf32>
          %mul = arith.mulf %a, %b : f32
          %sum = arith.addf %acc, %mul : f32
          scf.yield %sum : f32
        }
        %score = arith.mulf %dot, %scale : f32
        memref.store %score, %scores[%i, %j] : memref<?x?xf32>
        %newmax = arith.maximumf %oldmax, %score : f32
        scf.yield %newmax : f32
      }
      %denom = scf.for %j = %c0 to %limit step %c1 iter_args(%sum = %zero) -> f32 {
        %score = memref.load %scores[%i, %j] : memref<?x?xf32>
        %shifted = arith.subf %score, %max : f32
        %weight = math.exp %shifted : f32
        memref.store %weight, %scores[%i, %j] : memref<?x?xf32>
        %next = arith.addf %sum, %weight : f32
        scf.yield %next : f32
      }
      %has_keys = arith.cmpi ugt, %limit, %c0 : index
      scf.for %col = %c0 to %p step %c1 {
        %weighted = scf.for %j = %c0 to %limit step %c1 iter_args(%acc = %zero) -> f32 {
          %weight = memref.load %scores[%i, %j] : memref<?x?xf32>
          %value = memref.load %v[%j, %col] : memref<?x?xf32>
          %mul = arith.mulf %weight, %value : f32
          %next = arith.addf %acc, %mul : f32
          scf.yield %next : f32
        }
        %result = scf.if %has_keys -> f32 {
          %normalized = arith.divf %weighted, %denom : f32
          scf.yield %normalized : f32
        } else {
          scf.yield %zero : f32
        }
        memref.store %result, %out[%i, %col] : memref<?x?xf32>
      }
    }
    memref.dealloc %scores : memref<?x?xf32>
    return
  }
}
