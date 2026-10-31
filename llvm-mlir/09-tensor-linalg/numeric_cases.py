"""Build a deterministic MLIR driver that checks complete small tensor results."""
from pathlib import Path


def build_driver(project: Path, overrides=None):
    functions = []
    overrides = overrides or {}
    for p in sorted(project.glob('*.mlir')):
        source = overrides.get(p.stem, p.read_text()).strip()
        assert source.startswith('module {') and source.endswith('}')
        functions.append(source[len('module {'):-1])
    # Change a single semantic condition: nonzero init, or empty reduction domain.
    reduction = (project / 'row-sum.mlir').read_text().strip()[len('module {'):-1]
    functions.append(reduction.replace('@row_sum', '@row_sum_ten').replace('constant 0.0', 'constant 10.0'))
    functions.append(reduction.replace('@row_sum', '@row_sum_empty').replace('tensor<2x3xf32>', 'tensor<2x0xf32>'))
    lines = ['  func.func @main() -> i32 {']
    serial = 0
    failures = []
    observations = []
    current_call = ''

    def emit(expression):
        nonlocal serial
        name = f'%v{serial}'
        serial += 1
        lines.append(f'    {name} = {expression}')
        return name

    indices = [emit(f'arith.constant {i} : index') for i in range(5)]

    def scalar(value, typ='f32'):
        text = str(float(value)) if typ == 'f32' else str(value)
        return emit(f'arith.constant {text} : {typ}')

    def tensor(data, shape, element='f32'):
        def dense(x):
            if isinstance(x, list):
                return '[' + ', '.join(dense(v) for v in x) + ']'
            return str(float(x)) if element == 'f32' else str(x)
        typ = 'tensor<' + 'x'.join(str(d) for d in shape) + 'x' + element + '>'
        text = '' if any(d == 0 for d in shape) else dense(data)
        return emit(f'arith.constant dense<{text}> : {typ}'), typ

    def compare(value, expected, typ='f32', position='scalar'):
        if typ == 'f32':
            lines.append(f'    call @printF32({value}) : (f32) -> ()')
        else:
            wide = emit(f'arith.index_cast {value} : index to i64') if typ == 'index' else emit(f'arith.extsi {value} : i32 to i64')
            lines.append(f'    call @printI64({wide}) : (i64) -> ()')
        lines.append('    call @printNewline() : () -> ()')
        observations.append({'function': current_call, 'position': position, 'expected': expected})
        constant = scalar(expected, typ)
        cmp = emit(f'arith.cmpf une, {value}, {constant} : f32') if typ == 'f32' else emit(f'arith.cmpi ne, {value}, {constant} : {typ}')
        failures.append(emit(f'arith.extui {cmp} : i1 to i32'))

    def check_tensor(value, typ, expected, element='f32'):
        def walk(data, path):
            if isinstance(data, list):
                for i, part in enumerate(data): walk(part, path + [i])
            else:
                v = emit(f'tensor.extract {value}[' + ', '.join(indices[i] for i in path) + f'] : {typ}')
                result_name = 'result' + (value.split('#')[-1] if '#' in value else '')
                compare(v, data, element, result_name + '[' + ','.join(map(str, path)) + ']')
        walk(expected, [])

    def call(name, operands, types, result):
        nonlocal current_call
        current_call = name
        return emit(f'call @{name}(' + ', '.join(operands) + ') : (' + ', '.join(types) + f') -> {result}')

    a, at = tensor([[1,2,3],[4,5,6]], [2,3])
    b, bt = tensor([[10,20,30],[40,50,60]], [2,3])
    r = call('add', [a,b], [at,bt], at)
    check_tensor(r,at,[[11,22,33],[44,55,66]])
    bias, bit = tensor([10,20,30], [3])
    r = call('bias', [a,bias], [at,bit], at)
    check_tensor(r,at,[[11,22,33],[14,25,36]])
    r = call('row_sum',[a],[at],'tensor<2xf32>')
    check_tensor(r,'tensor<2xf32>',[6,15])
    r = call('row_sum_ten',[a],[at],'tensor<2xf32>')
    check_tensor(r,'tensor<2xf32>',[16,25])
    empty_reduction, ert = tensor([], [2,0])
    r = call('row_sum_empty',[empty_reduction],[ert],'tensor<2xf32>')
    check_tensor(r,'tensor<2xf32>',[0,0])
    mb, mbt = tensor([[1,2],[3,4],[5,6]],[3,2])
    r = call('matmul',[a,mb],[at,mbt],'tensor<2x2xf32>')
    check_tensor(r,'tensor<2x2xf32>',[[22,28],[49,64]])
    r = call('add_preserve',[a,b],[at,bt],f'({at}, {at})')
    # Multiple call results use MLIR's result-group notation.
    lines[-1] = lines[-1].replace(r+' =',r+':2 =')
    check_tensor(r+'#0',at,[[1,2,3],[4,5,6]])
    check_tensor(r+'#1',at,[[11,22,33],[44,55,66]])
    value = scalar(99)
    r = call('update',[a,value],[at,'f32'],f'(f32, f32, {at})')
    lines[-1] = lines[-1].replace(r+' =',r+':3 =')
    compare(r+'#0',2,position='old'); compare(r+'#1',99,position='new')
    check_tensor(r+'#2',at,[[1,99,3],[4,5,6]])
    grid, gt = tensor([[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,14,15]],[4,4],'i32')
    r = call('patch',[grid],[gt],f'(tensor<2x2xi32>, {gt})')
    lines[-1] = lines[-1].replace(r+' =',r+':2 =')
    check_tensor(r+'#0','tensor<2x2xi32>',[[5,6],[9,10]],'i32')
    check_tensor(r+'#1',gt,[[0,1,2,3],[4,99,6,7],[8,9,10,11],[12,13,14,15]],'i32')
    r = call('subsample',[grid],[gt],'tensor<2x2xi32>')
    check_tensor(r,'tensor<2x2xi32>',[[0,2],[8,10]],'i32')
    r = call('row',[grid],[gt],'tensor<4xi32>')
    check_tensor(r,'tensor<4xi32>',[8,9,10,11],'i32')
    for name in ['reshape','reshape_shape']:
        r=call(name,[a],[at],'tensor<3x2xf32>')
        check_tensor(r,'tensor<3x2xf32>',[[1,2],[3,4],[5,6]])
    da=call('forget_rows',[a],[at],'tensor<?x3xf32>')
    db=emit(f'tensor.cast {b} : {bt} to tensor<?x3xf32>')
    r=call('shape',[da],['tensor<?x3xf32>'],'(index, index)')
    lines[-1]=lines[-1].replace(r+' =',r+':2 =')
    compare(r+'#0',2,'index',position='rows'); compare(r+'#1',3,'index',position='columns')
    r=call('flatten_restore',[da],['tensor<?x3xf32>'],'tensor<?x3xf32>')
    check_tensor(r,'tensor<?x3xf32>',[[1,2,3],[4,5,6]])
    r=call('add_dynamic',[da,db],['tensor<?x3xf32>']*2,'tensor<?x3xf32>')
    check_tensor(r,'tensor<?x3xf32>',[[11,22,33],[44,55,66]])
    dynamic_a=emit(f'tensor.cast {a} : {at} to tensor<?x?xf32>')
    r=call('window',[dynamic_a,indices[0],indices[1],indices[2],indices[2]],['tensor<?x?xf32>']+['index']*4,'tensor<?x?xf32>')
    check_tensor(r,'tensor<?x?xf32>',[[2,3],[5,6]])
    for rows in [0,2]:
        r=call('coordinates',[indices[rows]],['index'],'tensor<?x3xindex>')
        size=emit(f'tensor.dim {r}, {indices[0]} : tensor<?x3xindex>')
        compare(size,rows,'index')
        if rows: check_tensor(r,'tensor<?x3xindex>',[[0,1,2],[10,11,12]],'index')
    empty, et=tensor([], [0,3])
    de=emit(f'tensor.cast {empty} : {et} to tensor<?x3xf32>')
    r=call('add_dynamic',[de,de],['tensor<?x3xf32>']*2,'tensor<?x3xf32>')
    size=emit(f'tensor.dim {r}, {indices[0]} : tensor<?x3xf32>')
    compare(size,0,'index')
    total=scalar(0,'i32')
    for failed in failures: total=emit(f'arith.addi {total}, {failed} : i32')
    lines += [f'    return {total} : i32', '  }']
    declarations = ['  func.func private @printF32(f32)',
                    '  func.func private @printI64(i64)',
                    '  func.func private @printNewline()']
    return 'module {\n'+'\n'.join(declarations+functions+lines)+'\n}\n', observations
