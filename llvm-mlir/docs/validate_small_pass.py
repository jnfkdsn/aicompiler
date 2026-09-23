#!/usr/bin/env python3
"""Verify the first_pass chapter against its compiled tool and lit tests."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import textwrap
from validate_examples import EXAMPLE


def main():
    workspace = Path(__file__).resolve().parents[3]
    project = workspace / "aicompiler-labs/llvm-mlir/04-small-pass"
    page = workspace / "blog/docs/notes/compile/mlir/tutorials/first_pass.md"
    build = workspace / "artifacts/builds/mlir-small-pass"
    llvm = workspace / "artifacts/builds/mlir-20.1.8/bin"
    out = workspace / "artifacts/logs/mlir-docs" / datetime.now().strftime("%Y-%m-%d-small-pass")
    out.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, condition):
        checks.append({"name": name, "passed": bool(condition)})

    def run(name, cmd, expected=0, timeout=30):
        result = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, timeout=timeout)
        (out / (name + ".stdout.txt")).write_text(result.stdout)
        (out / (name + ".stderr.txt")).write_text(result.stderr)
        check(name, result.returncode == expected)
        return result

    observed = run("build-observe-lit", [sys.executable, project / "observe.py", "--test"], timeout=300)
    if observed.returncode:
        raise SystemExit(f"Build/observation/tests failed: {out}")
    content = page.read_text()
    source = "\n".join((project / name).read_text() for name in ("LabPass.cpp", "lab-opt.cpp"))
    regions = {name: textwrap.dedent(code).strip() for name, code in re.findall(
        r"// BEGIN: ([\w-]+)\n(.*?)\s*// END: \1", source, re.S)}
    snippets = re.findall(r"<!-- cpp-example: ([\w-]+) -->\s*```cpp\n(.*?)\n```", content, re.S)
    check("all-compiled-snippets", set(regions) == {n for n, _ in snippets} and len(regions) == len(snippets))
    for name, code in snippets:
        check("snippet-" + name, regions.get(name) == code.strip())
    test = (project / "tests/rewrite.mlir").read_text()
    check_block = re.search(r"```text\n(// CHECK-LABEL: func.func @twice\(.*?)\n```", content, re.S)[1]
    check("filecheck-example-from-test", check_block in test)
    run_line = re.search(r"^// RUN: .+$", content, re.M)[0]
    check("run-directive-from-test", run_line in test)
    examples = {spec.strip(): code for kind, spec, code in EXAMPLE.findall(content) if kind == "example"}
    check("expected-examples", set(examples) == {"first-pass-input", "first-pass-output"})
    normalized = {}
    for name, code in examples.items():
        path = out / (name + ".mlir")
        path.write_text(code + "\n")
        normalized[name] = run(name + "-verify", [llvm / "mlir-opt", path]).stdout.strip()
        generic = run(name + "-generic", [llvm / "mlir-opt", path, "--mlir-print-op-generic"])
        generic_path = out / (name + "-generic.mlir")
        generic_path.write_text(generic.stdout)
        run(name + "-roundtrip", [llvm / "mlir-opt", generic_path])
    pipeline = "builtin.module(func.func(lab-remove-add-zero))"
    result = run("document-output", [build / "lab-opt", out / "first-pass-input.mlir",
                                    "--pass-pipeline=" + pipeline, "--verify-each"])
    check("displayed-output", result.stdout.strip() == normalized["first-pass-output"])
    output = out / "actual-output.mlir"
    output.write_text(result.stdout)
    repeated = run("repeat", [build / "lab-opt", output, "--pass-pipeline=" + pipeline])
    check("stable-output", repeated.stdout == result.stdout)
    failure = run("wrong-anchor", [build / "lab-opt", out / "first-pass-input.mlir",
                                   "--pass-pipeline=builtin.module(lab-remove-add-zero)"], expected=1)
    check("anchor-diagnostic", "restricted to 'func.func'" in failure.stderr
          and "intended to run on 'builtin.module'" in failure.stderr)
    version = run("mlir-version", [llvm / "mlir-opt", "--version"]).stdout
    files = [page, Path(__file__).resolve(), *sorted(p for p in project.rglob("*") if p.is_file())]
    manifest = {"date": datetime.now().isoformat(), "llvm_version": version,
        "files_sha256": {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "checks": checks}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    failed = [c["name"] for c in checks if not c["passed"]]
    print(f"{len(checks)-len(failed)}/{len(checks)} checks passed; {out / 'manifest.json'}")
    if failed:
        raise SystemExit("Failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
