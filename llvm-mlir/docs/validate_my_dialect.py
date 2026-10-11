#!/usr/bin/env python3
"""Author regression for the minimal My dialect; never edit learner work/."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def main():
    workspace = Path(__file__).resolve().parents[3]
    project = workspace / 'aicompiler-labs/llvm-mlir/my-dialect'
    source = project / 'stages/01-minimal'
    chapter = workspace / 'blog/docs/notes/compile/mlir/compiler/ir_definition/dialect_basics.md'
    build = workspace / 'artifacts/builds/my-dialect-01'
    llvm = workspace / 'artifacts/builds/mlir-20.1.8'
    logs = workspace / 'artifacts/logs/mlir-docs' / (datetime.now().strftime('%Y-%m-%d-%H%M%S-%f') + '-my-dialect')
    logs.mkdir(parents=True)
    checks = []

    def check(name, condition):
        if not condition:
            raise RuntimeError(f'{name}: failed; logs: {logs}')
        checks.append(name)

    def run(name, command, expected=0, cwd=None, env=None):
        result = subprocess.run(list(map(str, command)), cwd=cwd or workspace,
                                env=env, capture_output=True, text=True, timeout=240)
        (logs / f'{name}.stdout.txt').write_text(result.stdout)
        (logs / f'{name}.stderr.txt').write_text(result.stderr)
        check(name + ': exit', result.returncode == expected)
        return result

    run('observe', [sys.executable, project / 'observe.py'])
    opt = build / 'my-opt'
    normal = run('custom', [opt, source / 'input.mlir']).stdout
    generic = run('generic', [opt, source / 'input.mlir', '--mlir-print-op-generic']).stdout
    generic_path = logs / 'generic.mlir'
    generic_path.write_text(generic)
    check('generic roundtrip', run('roundtrip', [opt, generic_path]).stdout == normal)
    # Check use-def relationships, not merely the presence of an operation name.
    flow = re.search(r'func.func @test\((%\w+): i32, (%\w+): i32\) -> i32 \{\s*'
                     r'(%\w+) = my.add (%\w+), (%\w+) : i32\s*return (%\w+) : i32', normal)
    check('operand and return relationships', flow is not None and
          flow.group(1) == flow.group(4) and flow.group(2) == flow.group(5) and flow.group(3) == flow.group(6))

    body = chapter.read_text()
    fragments = re.findall(r'<!-- my-(source|output): ([^ ]+) -->\s*```[^\n]*\n(.*?)\n```', body, re.S)
    check('chapter definition, input and output present',
          {('source', 'MyOps.td'), ('source', 'input.mlir'), ('output', 'custom')}
          <= {(kind, name) for kind, name, _ in fragments})
    for kind, name, code in fragments:
        expected = (source / name).read_text() if kind == 'source' else {'custom': normal, 'generic': generic}[name]
        check('chapter ' + name, code.strip() == expected.strip())
    generated = re.findall(r'<!-- my-generated: ([^ ]+) -->\s*```cpp\n(.*?)\n```', body, re.S)
    check('generated access, construction and name excerpts present',
          all(any(method in code for _, code in generated)
              for method in ['getLhs()', 'AddOp::build(', 'getOperationName()']))
    for n, (name, code) in enumerate(generated):
        # Excerpts may change indentation, but must preserve actual generated tokens.
        compact = lambda text: re.sub(r'\s+', '', text)
        check(f'generated excerpt {n}: {name}', bool(code.strip()) and compact(code) in compact((build / name).read_text()))

    for kind, name, code in re.findall(
            r'<!-- my-(source|output)-fragment: ([^ ]+) -->\s*```[^\n]*\n(.*?)\n```', body, re.S):
        expected = (source / name).read_text() if kind == 'source' else {'custom': normal, 'generic': generic}[name]
        check('chapter excerpt ' + name, re.sub(r'\s+', '', code) in re.sub(r'\s+', '', expected))

    # Check the commands used to explain generation and printing. The article
    # need not reproduce the lab's configuration or full build instructions.
    commands = re.findall(r'<!-- my-command: ([^ ]+) -->\s*```bash\n(.*?)\n```', body, re.S)
    check('chapter observation commands present',
          {'tblgen', 'run', 'generic'} <= {name for name, _ in commands})
    command_dir = logs / 'chapter-commands'
    command_dir.mkdir()
    for name in ['MyOps.td', 'input.mlir']:
        shutil.copy2(source / name, command_dir / name)
    (command_dir / 'my-opt').symlink_to(opt)
    command_env = os.environ.copy()
    command_env['PATH'] = str(llvm / 'bin') + os.pathsep + command_env.get('PATH', '')
    command_env['MLIR_INCLUDE_DIR'] = str(workspace / 'upstream/llvm-project/mlir/include')
    for name, command in commands:
        result = run('chapter-command-' + name, ['bash', '-e', '-c', command],
                     cwd=command_dir, env=command_env)
        if name in ('run', 'generic'):
            check('chapter command output ' + name, result.stdout == (normal if name == 'run' else generic))
    check('standalone TableGen matches CMake',
          (command_dir / 'MyOps.h.inc').read_bytes() == (build / 'MyOps.h.inc').read_bytes())

    invalid_examples = re.findall(
        r'<!-- my-invalid: ([^ ]+) \| (.*?) -->\s*```[^\n]*\n(.*?)\n```', body, re.S)
    check('chapter invalid type example present', any(name == 'operand-type' for name, _, _ in invalid_examples))
    for name, diagnostic, code in invalid_examples:
        path = logs / f'chapter-invalid-{name}.mlir'
        path.write_text(code + '\n')
        result = run('chapter-invalid-' + name, [opt, path], expected=1)
        check('chapter invalid diagnostic ' + name, diagnostic in result.stderr)
    header = (build / 'MyOps.h.inc').read_text()
    impl = (build / 'MyOps.cpp.inc').read_text()
    for method in ['getLhs()', 'getRhs()', 'getResult()']:
        check('generated ' + method, method in header)
    for method in ['build', 'parse', 'print', 'verifyInvariants']:
        check('generated AddOp::' + method, 'AddOp::' + method in impl)

    cases = {
        'operand-type': ('i64, %b: i32', '"my.add"(%a, %b) : (i64, i32) -> i32', 'operand #0 must be 32-bit signless integer'),
        'result-type': ('i32, %b: i32', '"my.add"(%a, %b) : (i32, i32) -> i64', 'result #0 must be 32-bit signless integer'),
        'operand-count': ('i32, %b: i32', '"my.add"(%a) : (i32) -> i32', 'expected 2 operands'),
        'unknown-op': ('i32, %b: i32', '"my.unknown"(%a, %b) : (i32, i32) -> i32', 'unregistered operation'),
    }
    for name, (args, operation, diagnostic) in cases.items():
        path = logs / f'{name}.mlir'
        path.write_text(f'module {{\n  func.func @bad(%a: {args}) {{\n    %0 = {operation}\n    return\n  }}\n}}\n')
        result = run(name, [opt, path], expected=1)
        check(name + ': diagnostic', diagnostic in result.stderr)

    # Check the proposed exercise using an author-owned copy, outside work/.
    task_source = logs / 'rename-source'
    task_build = logs / 'rename-build'
    shutil.copytree(source, task_source)
    td = task_source / 'MyOps.td'
    td.write_text(td.read_text().replace('$lhs', '$left'))
    # Compile the article's equivalent registration spelling in the author
    # copy, after checking that the actual generated list contains only AddOp.
    equivalent = re.search(r'<!-- my-equivalent: initialize -->\s*```cpp\n(.*?)\n```', body, re.S)
    check('equivalent registration snippet present', equivalent is not None)
    op_list = re.search(r'#ifdef GET_OP_LIST\s*#undef GET_OP_LIST\s*(.*?)\s*#endif', impl, re.S)
    check('generated registration list is AddOp', op_list is not None and op_list.group(1).strip() == '::mlir::my::AddOp')
    cpp = task_source / 'MyOps.cpp'
    changed, replacements = re.subn(r'void MyDialect::initialize\(\) \{.*?\n\}',
                                   lambda _: equivalent.group(1), cpp.read_text(), flags=re.S)
    check('registration implementation replaced once', replacements == 1)
    cpp.write_text(changed)
    run('rename-configure', ['cmake', '-S', task_source, '-B', task_build, '-G', 'Ninja',
        f'-DMLIR_DIR={llvm}/lib/cmake/mlir', f'-DLLVM_DIR={llvm}/lib/cmake/llvm',
        '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CXX_COMPILER=/usr/bin/clang++', '-DCMAKE_C_COMPILER=/usr/bin/clang'])
    run('rename-build', ['cmake', '--build', task_build, '-j2'])
    renamed_header = (task_build / 'MyOps.h.inc').read_text()
    check('renamed accessor', 'getLeft()' in renamed_header and 'getLhs()' not in renamed_header)
    check('rename preserves printed IR', run('rename-print', [task_build / 'my-opt', task_source / 'input.mlir']).stdout == normal)

    for page in chapter.parent.glob('*.md'):
        for relative in re.findall(r'https://github.com/jnfkdsn/aicompiler/(?:blob|tree)/main/([^\s)]+)', page.read_text()):
            check('cross-repo target ' + relative, (workspace / 'aicompiler-labs' / relative).exists())
    inputs = [chapter, Path(__file__), project / 'observe.py', *sorted(source.iterdir())]
    manifest = {'checks': checks, 'llvm': 'llvmorg-20.1.8', 'scope': 'compiler-side; no target execution',
                'sha256': {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    (logs / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(checks)} checks passed. Logs: {logs}')


if __name__ == '__main__':
    main()
