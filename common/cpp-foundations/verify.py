#!/usr/bin/env python3
"""Verify the C++ bridge chapters against their executable sources."""
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess


def main():
    source = Path(__file__).resolve().parent
    root = source.parents[2]
    out = root / 'artifacts/builds/cpp-foundations'
    out.mkdir(parents=True, exist_ok=True)
    logs = root / 'artifacts/logs/cpp-foundations' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    logs.mkdir(parents=True)
    checks = []

    def check(name, passed):
        if not passed:
            raise RuntimeError(f'{name}: failed; logs: {logs}')
        checks.append(name)

    def run(name, command, failure=False):
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=120)
        (logs / (name + '.stdout')).write_text(result.stdout)
        (logs / (name + '.stderr')).write_text(result.stderr)
        check(name + ': exit', result.returncode != 0 if failure else result.returncode == 0)
        return result

    setup = 'CPP_LAB="$PWD/aicompiler-labs/common/cpp-foundations"\nCPP_OUT="$PWD/artifacts/builds/cpp-foundations"\n'
    outputs = []
    for chapter in ['source_to_program', 'generated_cpp', 'template_calls']:
        text = (root / 'blog/docs/notes/cpp' / (chapter + '.md')).read_text()
        for name, code in re.findall(r'<!-- cpp-source: ([^ ]+) -->\s*```[^\n]*\n(.*?)\n```', text, re.S):
            check('source ' + name, code.strip() == (source / name).read_text().strip())
        for n, command in enumerate(re.findall(r'```bash\n(.*?)\n```', text, re.S)):
            failure = '-o "$CPP_OUT/missing"' in command
            result = run(f'{chapter}-{n}', ['bash', '-e', '-c', setup + command], failure)
            if failure:
                check('missing implementation diagnostic', 'undefined reference' in result.stderr and 'add(int, int)' in result.stderr)
        outputs.extend(re.findall(r'<!-- cpp-output: ([^ ]+) -->\s*```[^\n]*\n(.*?)\n```', text, re.S))

    for name in ['single', 'demo', 'demo-library', 'generated-demo']:
        check(name + ': result', run(name, [str(out / name)]).stdout == '5\n')
    template = run('template-output', [str(out / 'template-demo')]).stdout
    compact = lambda text: re.sub(r'\s+', '', text)
    check('same preprocessed program', compact((out / 'add.ii').read_text()) == compact((out / 'generated-add.ii').read_text()))
    expected_outputs = {'preprocessed': (out / 'add.ii').read_text(), 'generated': (out / 'generated.inc').read_text(), 'template': template}
    for name, code in outputs:
        check('document output ' + name, compact(code) == compact(expected_outputs[name]))

    base = ['c++', '-std=c++17', '-E', '-P', '-x', 'c++']
    nothing = run('no-selection', base + [str(out / 'generated.inc')]).stdout
    check('unselected fragments absent', not nothing.strip())
    declarations = run('declarations', base + ['-DSELECT_DECLARATIONS', str(out / 'generated.inc')]).stdout
    check('declarations only', compact(declarations) == 'intadd(inta,intb);')
    definitions = run('definitions', base + ['-DSELECT_DEFINITIONS', str(out / 'generated.inc')]).stdout
    check('definitions only', compact(definitions) == 'intadd(inta,intb){returna+b;}')
    invalid = logs / 'invalid-template.cpp'
    invalid.write_text((source / 'templates/main.cpp').read_text().replace('announce<AddTag>', 'announce<int>'))
    error = run('invalid-template', ['c++', '-std=c++17', '-c', str(invalid), '-o', str(logs / 'invalid.o')], True)
    check('template diagnostic mentions name', 'name' in error.stderr)
    (logs / 'checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(checks)} checks passed. Logs: {logs}')


if __name__ == '__main__':
    main()
