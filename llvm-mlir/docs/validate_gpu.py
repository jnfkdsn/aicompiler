#!/usr/bin/env python3
"""Validate GPU representations, compile artifacts and logical models separately."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

WORKSPACE = Path(__file__).resolve().parents[3]
PROJECT = WORKSPACE / 'aicompiler-labs/llvm-mlir/16-gpu-execution'
sys.path.insert(0, str(PROJECT))
from experiment import Experiment, LLVM, OPT, log_directory


def main():
    out = log_directory()
    e = Experiment(out)
    e.check('version', '20.1.8' in e.run('version', [OPT, '--version']).stdout)
    for p in PROJECT.glob('*.mlir'):
        normal = e.artifact('parse-' + p.stem, [OPT, p])
        generic = e.artifact('generic-' + p.stem, [OPT, p, '--mlir-print-op-generic'])
        again = e.artifact('reparse-' + p.stem, [OPT, generic])
        e.check('roundtrip-' + p.stem, normal.read_text() == again.read_text())
    parallel, forall = e.mapping()
    for name, p in [('parallel', parallel), ('forall', forall)]:
        code = p.read_text()
        e.check(name + '-launch', code.count('gpu.launch ') == 1 and 'scf.parallel' not in code and 'scf.forall' not in code)
        e.check(name + '-guard', 'arith.cmpi ult' in code and code.count('memref.load') == 1 and code.count('memref.store') == 1)
    outputs = e.lowering()
    launch = (out / 'launch-outlined.mlir').read_text()
    e.check('outlining-boundary', 'gpu.launch_func' in launch and 'gpu.func @' in launch and 'gpu.launch ' not in launch)
    e.check('launch-shape', 'known_block_size = array<i32: 4, 1, 1>' in launch and 'known_grid_size = array<i32: 3, 1, 1>' in launch)
    lowered = outputs['launch'].read_text()
    e.check('device-identifiers', 'nvvm.read.ptx.sreg.tid.x' in lowered and 'nvvm.read.ptx.sreg.ctaid.x' in lowered)
    e.check('device-guard-retained', 'llvm.cond_br' in lowered and 'llvm.load' in lowered and 'llvm.store' in lowered)
    shared = outputs['shared'].read_text()
    e.check('barrier-lowered', 'nvvm.barrier0' in shared and 'gpu.barrier' not in shared)
    e.check('address-spaces', '!llvm.ptr<1>' in shared and '!llvm.ptr<3>' in shared and 'addr_space = 3' in shared)
    e.check('private-stack', 'llvm.alloca' in shared)
    host = outputs['host'].read_text()
    e.check('host-launch-retained', 'gpu.launch_func' in host and 'llvm.call @mgpuLaunchKernel' not in host)
    calls = re.findall(r'llvm.call @([\w]+)', host)
    for name, count in [('mgpuMemHostRegisterMemRef', 2), ('mgpuMemHostUnregisterMemRef', 2),
                        ('mgpuMemAlloc', 2), ('mgpuMemFree', 2), ('mgpuMemcpy', 2), ('mgpuStreamSynchronize', 1)]:
        e.check('host-' + name, calls.count(name) == count)
    e.check('wait-before-unregister', host.index('llvm.call @mgpuStreamSynchronize') < host.index('llvm.call @mgpuMemHostUnregisterMemRef'))
    r = e.run('missing-binary', [LLVM / 'bin/mlir-translate', outputs['host'], '--mlir-to-llvmir'], expected=1)
    e.check('missing-binary-diagnostic', "Couldn't find the binary holding the kernel" in r.stderr)
    # The fixed mapping rejects a block too small for four simultaneous iterations.
    bad = out / 'small-block.mlir'
    bad.write_text((PROJECT / 'map-forall.mlir').read_text().replace('block_dims = [4, 1, 1]', 'block_dims = [2, 1, 1]'))
    r = e.run('small-block', [OPT, PROJECT / 'forall.mlir',
        '--transform-preload-library=transform-library-paths=' + str(bad), '--transform-interpreter'], expected=1)
    e.check('small-block-diagnostic', 'thread' in r.stderr.lower())
    data = e.models()
    for row in data['coverage']:
        e.check(f"coverage-{row['n']}-{row['block']}", all(v == 1 for v in row['visits']) and
            all(row['n'] <= i < row['groups'] * row['block'] for i in row['inactive']))
    order = data['interleavings']
    e.check('interleaving-counts', [order[k] for k in ['thread_order_respecting', 'read_before_write', 'all_writes_before_reads']] == [2520, 1432, 576])
    e.check('bank-model', len(set(data['banks32'])) == 1 and len(set(data['banks33'])) == 32)
    e.check('overwrite-counterexample', data['double_buffer']['broken_read'] == [10, 60] and data['double_buffer']['intended_read'] == [10, 20])
    if '--without-serialization' not in sys.argv:
        e.check('ptxas-version', 'release 12.4' in e.run('ptxas-version', ['/usr/local/cuda/bin/ptxas', '--version']).stdout)
        encoded = e.serialize()
        for name in ['async', 'shared']:
            ptx = encoded[name]['ptx'].read_text()
            e.check('ptx-' + name, '.target sm_80' in ptx and '.visible .entry' in ptx)
            e.check('cubin-' + name, encoded[name]['cubin'].read_bytes()[:4] == b'\x7fELF')
        e.check('ptx-shared-barrier', 'bar.sync' in encoded['shared']['ptx'].read_text())
        e.check('shown-shared-resources', 'Used 12 registers, 16 bytes smem' in (out / 'shared-ptxas.stderr.txt').read_text())
        translated = encoded['host'].read_text()
        for name in ['mgpuModuleLoad', 'mgpuModuleGetFunction', 'mgpuLaunchKernel']:
            e.check('translated-' + name, '@' + name in translated)
        e.check('translated-no-gpu-ops', 'gpu.launch_func' not in translated)
    # Record source evidence as source evidence, never as an NPU build/run.
    npu = WORKSPACE / 'upstream/AscendNPU-IR'
    commit = subprocess.check_output(['git', '-C', str(npu), 'rev-parse', 'HEAD'], text=True).strip()
    e.check('npu-snapshot', commit == '37c6ebc33d1789500014e6a7b2b62164b3cb566b')
    source_names = ['bishengir/include/bishengir/Dialect/HIVM/IR/HIVMVectorOps.td',
        'bishengir/include/bishengir/Dialect/HIVM/IR/HIVMDMAOps.td',
        'bishengir/lib/Dialect/HIVM/Pipelines/HIVMPipelines.cpp',
        'bishengir/test/Integration/HIVM/VecAdd/add.mlir']
    texts = [(npu / name).read_text() for name in source_names]
    e.check('npu-add-definition', 'def VAddOp : HIVM_ElementwiseBinaryOp<"vadd"' in texts[0])
    e.check('npu-dma-pipe', 'PIPE_MTE2' in texts[1] and 'PIPE_MTE3' in texts[1])
    e.check('npu-memory-planning', 'createPlanMemoryPass' in texts[2] and 'createEnableMultiBufferPass' in texts[2])
    e.check('npu-integration-operations', all(s in texts[3] for s in ['hivm.hir.load', 'hivm.hir.vadd', 'hivm.hir.store']))
    root = WORKSPACE / 'blog/docs/notes/compile/mlir'
    files = [*(root / 'dialects/gpu').glob('*.md'), *(root / 'compiler/targets').glob('*.md'),
        Path(__file__).resolve(), *(p for p in PROJECT.iterdir() if p.is_file())]
    manifest = {'date': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'llvm_commit': '87f0227cb60147a26a1eeb4fb06e3b505e9c7261', 'npu_commit': commit,
        'device_execution': False, 'serialization': '--without-serialization' not in sys.argv,
        'scope': 'IR roundtrips, mapping/outlining/NVVM/host wrappers; optional PTX/cubin and host-object compilation; separate finite logical models and pinned NPU source checks. No GPU/NPU execution or performance evidence.',
        'files_sha256': {str(p.relative_to(WORKSPACE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'npu_source_sha256': {name: hashlib.sha256((npu / name).read_bytes()).hexdigest() for name in source_names},
        'checks': e.checks}
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    failed = [c['name'] for c in e.checks if not c['passed']]
    print(f'{len(e.checks) - len(failed)}/{len(e.checks)} checks passed; device execution: false')
    print(out / 'manifest.json')
    if failed:
        raise SystemExit('Failed: ' + ', '.join(failed))


if __name__ == '__main__':
    main()
