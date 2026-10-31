"""Small initialized inputs, concrete expected values, and native observation."""
from pathlib import Path

PROJECT = Path(__file__).resolve().parent


def build_driver(suite):
    names = (['storage', 'dynamic', 'view', 'nested-view', 'cast'] if suite == 'manual'
             else ['reuse', 'preserve', 'readonly', 'fill-preserve', 'call',
                   'return-alias', 'branch', 'signature', 'tile-update'])
    bodies = [((PROJECT / (name + '.mlir')).read_text().strip()[len('module {'):-1]).strip()
              for name in names]
    lines, expected = [], []
    def emit(line):
        lines.append('    ' + line)
    def observe(value, typ, name, result):
        n = len(expected)
        emit(f'%obs{n} = arith.' + ('index_cast' if typ == 'index' else 'extsi') + f' {value} : {typ} to i64')
        emit(f'func.call @printI64(%obs{n}) : (i64) -> ()')
        emit('func.call @printNewline() : () -> ()')
        expected.append({'name': name, 'expected': result})
    def init_vector():
        emit('%m = memref.alloc() : memref<4xi32>')
        for i, v in enumerate((10, 20, 30, 40)):
            emit(f'%v{i} = arith.constant {v} : i32')
            emit(f'memref.store %v{i}, %m[%c{i}] : memref<4xi32>')
    def init_matrix():
        emit('%matrix = memref.alloc() : memref<4x4xi32>')
        for i in range(4):
            for j in range(4):
                emit(f'%a{i}{j} = arith.constant {4*i+j} : i32')
                emit(f'memref.store %a{i}{j}, %matrix[%c{i}, %c{j}] : memref<4x4xi32>')
    for i in range(6):
        emit(f'%c{i} = arith.constant {i} : index')
    if suite == 'manual':
        emit('%s = func.call @storage() : () -> i32'); observe('%s', 'i32', 'storage', 7)
        emit('%d = func.call @dynamic(%c5) : (index) -> index'); observe('%d', 'index', 'dynamic-rows', 5)
        init_matrix()
        emit('%n:2 = func.call @nested(%matrix) : (memref<4x4xi32>) -> (i32, i32)')
        observe('%n#0', 'i32', 'nested-origin', 9); observe('%n#1', 'i32', 'strided-origin', 10)
        emit('%cast = func.call @cast_view(%matrix) : (memref<4x4xi32>) -> i32')
        observe('%cast', 'i32', 'dynamic-layout-same-element', 6)
        emit('%w:4 = func.call @window(%matrix) : (memref<4x4xi32>) -> (i32, index, index, index)')
        for i, (typ, name, val) in enumerate([('i32','alias-write',99),('index','offset',5),('index','row-stride',4),('index','column-stride',1)]):
            observe(f'%w#{i}',typ,name,val)
        emit('%tile = memref.subview %matrix[1, 1][2, 2][1, 1] : memref<4x4xi32> to memref<2x2xi32, strided<[4, 1], offset: 5>>')
        emit('%packed = memref.alloc() : memref<2x2xi32>')
        emit('memref.copy %tile, %packed : memref<2x2xi32, strided<[4, 1], offset: 5>> to memref<2x2xi32>')
        emit('%copied = memref.load %packed[%c1, %c0] : memref<2x2xi32>')
        observe('%copied','i32','copy-respects-strides',9)
        emit('%x = arith.constant 77 : i32')
        emit('memref.store %x, %packed[%c0, %c0] : memref<2x2xi32>')
        emit('%old = memref.load %matrix[%c1, %c1] : memref<4x4xi32>')
        observe('%old','i32','copied-storage-independent',5)
        emit('memref.dealloc %packed : memref<2x2xi32>')
        emit('memref.dealloc %matrix : memref<4x4xi32>')
    else:
        init_vector()
        emit('%p:3 = func.call @preserve(%m) : (memref<4xi32>) -> (i32, i32, i32)')
        for i,v in enumerate((10,99,20)): observe(f'%p#{i}','i32',f'preserve-{i}',v)
        emit('%ro = func.call @readonly(%m) : (memref<4xi32>) -> i32');observe('%ro','i32','readonly-result',99)
        emit('%afterro = memref.load %m[%c0] : memref<4xi32>');observe('%afterro','i32','readonly-input',10)
        emit('%f:2 = func.call @fill_preserve(%m) : (memref<4xi32>) -> (i32, i32)')
        observe('%f#0','i32','fill-old',10);observe('%f#1','i32','fill-new',99)
        emit('%r = func.call @reuse(%m) : (memref<4xi32>) -> i32');observe('%r','i32','reuse-result',99)
        emit('%after = memref.load %m[%c0] : memref<4xi32>');observe('%after','i32','reuse-input',99)
        emit('memref.store %v0, %m[%c0] : memref<4xi32>')
        emit('%q = func.call @consume() : () -> i32');observe('%q','i32','returned-allocation',42)
        emit('%true = arith.constant true');emit('%false = arith.constant false')
        for flag, val in [('true',77),('false',10)]:
            emit(f'%b{flag} = func.call @choose(%m, %{flag}) : (memref<4xi32>, i1) -> i32')
            observe(f'%b{flag}','i32','branch-'+flag,val)
        emit('%t = bufferization.to_tensor %m restrict writable : memref<4xi32> to tensor<4xi32>')
        emit('%u = func.call @updated(%t) : (tensor<4xi32>) -> tensor<4xi32>')
        emit('%uv = tensor.extract %u[%c0] : tensor<4xi32>');observe('%uv','i32','tensor-function-boundary',99)
        emit('%copy = func.call @return_alias(%m) : (memref<4xi32>) -> memref<4xi32>')
        emit('%cv = memref.load %copy[%c1] : memref<4xi32>');observe('%cv','i32','return-copy-content',20)
        emit('%mp = memref.extract_aligned_pointer_as_index %m : memref<4xi32> -> index')
        emit('%cp = memref.extract_aligned_pointer_as_index %copy : memref<4xi32> -> index')
        emit('%different = arith.cmpi ne, %mp, %cp : index')
        emit('%distinct = arith.select %different, %c1, %c0 : index')
        observe('%distinct','index','concrete-clone-lowering-distinct-storage',1)
        init_matrix()
        emit('%tile:2 = func.call @tile_update(%matrix) : (memref<4x4xi32>) -> (i32, i32)')
        observe('%tile#0','i32','tile-inside',99);observe('%tile#1','i32','tile-outside',0)
    emit('%ok = arith.constant 0 : i32');emit('return %ok : i32')
    return ('module {\n' + '\n'.join(bodies) + '\n  func.func private @printI64(i64)\n'
            '  func.func private @printNewline()\n  func.func @main() -> i32 {\n' +
            '\n'.join(lines) + '\n  }\n}\n'), expected
