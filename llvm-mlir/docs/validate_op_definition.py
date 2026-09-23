#!/usr/bin/env python3
"""Compile and verify the custom-dialect examples in op_definition.md."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import textwrap


def main():
    workspace = Path(__file__).resolve().parents[3]
    project = workspace / "aicompiler-labs/llvm-mlir/05-op-definition"
    page = workspace / "blog/docs/notes/compile/mlir/compiler/ir_definition/op_definition.md"
    build = workspace / "artifacts/builds/mlir-op-definition"
    llvm = workspace / "artifacts/builds/mlir-20.1.8/bin"
    out = workspace / "artifacts/logs/mlir-docs" / datetime.now().strftime("%Y-%m-%d-op-definition")
    out.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, condition):
        checks.append({"name": name, "passed": bool(condition)})

    def run(name, command, expected=0, timeout=30):
        command = [str(x) for x in command]
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        (out / (name + ".stdout.txt")).write_text(result.stdout)
        (out / (name + ".stderr.txt")).write_text(result.stderr)
        checks.append({"name": name, "command": command, "exit_code": result.returncode,
                       "passed": result.returncode == expected})
        return result

    result = run("build-observe-lit", [sys.executable, project / "observe.py", "--test"], timeout=300)
    if result.returncode:
        raise SystemExit(f"Build/observation/lit failed: {out}")
    content = page.read_text()
    sources = "\n".join(p.read_text() for p in sorted(project.iterdir()) if p.suffix in (".cpp", ".td"))
    regions = {name: textwrap.dedent(code).strip() for name, code in re.findall(
        r"// BEGIN: ([\w-]+)\n(.*?)\s*// END: \1", sources, re.S)}
    snippets = re.findall(r"<!-- source-example: ([\w-]+) -->\s*```(?:cpp|text)\n(.*?)\n```", content, re.S)
    check("all-source-regions", set(regions) == {n for n, _ in snippets} and len(regions) == len(snippets))
    for name, code in snippets:
        check("source-" + name, regions.get(name) == code.strip())
    matches = re.findall(r"<!-- lab-(example|invalid): ([^\n]+?) -->\s*```text\n(.*?)\n```", content, re.S)
    examples = {spec.split("|", 1)[0].strip(): code for kind, spec, code in matches if kind == "example"}
    check("unique-example-ids", len({spec.split('|', 1)[0].strip() for _, spec, _ in matches}) == len(matches))
    check("expected-inputs", set(examples) == {"op-definition-input", "op-definition-custom",
                                             "op-definition-generic", "op-definition-expanded"})
    opt = build / "lab-dialect-opt"
    for kind, spec, code in matches:
        parts = spec.split("|", 1)
        name = parts[0].strip()
        path = out / (name + ".mlir")
        path.write_text(code + "\n")
        result = run(name, [opt, path], expected=1 if kind == "invalid" else 0)
        if kind == "invalid":
            check(name + "-diagnostic", len(parts) == 2 and parts[1].strip() in result.stderr)
        else:
            generic = run(name + "-generic", [opt, path, "--mlir-print-op-generic"])
            generic_path = out / (name + "-generic.mlir")
            generic_path.write_text(generic.stdout)
            reparsed = run(name + "-roundtrip", [opt, generic_path])
            check(name + "-roundtrip-equal", reparsed.stdout == result.stdout)
    base = out / "op-definition-input.mlir"
    custom = run("display-custom", [opt, base])
    generic = run("display-generic", [opt, base, "--mlir-print-op-generic"])
    expanded = run("display-expanded", [opt, base, "--pass-pipeline=builtin.module(func.func(lab-expand-clamp))", "--verify-each"])
    for mode, result in [("custom", custom), ("generic", generic), ("expanded", expanded)]:
        check("displayed-" + mode, result.stdout.strip() == examples["op-definition-" + mode].strip())
    expanded_path = out / "actual-expanded.mlir"
    expanded_path.write_text(expanded.stdout)
    run("expanded-standard-tool", [llvm / "mlir-opt", expanded_path])
    made = run("builder", [build / "lab-build"])
    check("builder-equals-parsed", made.stdout == custom.stdout)
    check("builder-accessors", "builder completed; input_type=i32 lower=-4 upper=7" in made.stderr)
    rejected = run("builder-invalid", [build / "lab-build", "invalid"], expected=1)
    check("builder-does-not-auto-verify", "builder completed; input_type=i32 lower=8 upper=7" in rejected.stderr
          and "requires lower <= upper (signed i32)" in rejected.stderr)
    header, impl = (build / "LabOps.h.inc").read_text(), (build / "LabOps.cpp.inc").read_text()
    for token in ("getInput()", "getLowerAttr()", "getResult()", "uint32_t getLower();"):
        check("generated-" + token, token in header)
    check("generated-builder-properties", "odsState.getOrAddProperties<Properties>().lower = lower;" in impl)
    check("generated-before-custom-verification",
          "succeeded(verifyInvariantsImpl()) && ::mlir::succeeded(verify())" in impl)
    version = run("mlir-version", [llvm / "mlir-opt", "--version"]).stdout
    files = [page, Path(__file__).resolve(), *sorted(p for p in project.rglob("*")
             if p.is_file() and "__pycache__" not in p.parts), *sorted(build.glob("*.inc"))]
    manifest = {"date": datetime.now().isoformat(), "llvm_version": version,
        "files_sha256": {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "checks": checks}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    failures = [c["name"] for c in checks if not c["passed"]]
    print(f"{len(checks)-len(failures)}/{len(checks)} checks passed; {out / 'manifest.json'}")
    if failures:
        raise SystemExit("Failed: " + ", ".join(failures))


if __name__ == "__main__":
    main()
