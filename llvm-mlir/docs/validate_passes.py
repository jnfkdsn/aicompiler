#!/usr/bin/env python3
"""Check the worked examples and pipeline observations in compiler/transforms/passes.md."""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess

from validate_examples import EXAMPLE


def main():
    workspace = Path(__file__).resolve().parents[3]
    page = workspace / "blog/docs/notes/compile/mlir/compiler/transforms/passes.md"
    opt = workspace / "artifacts/builds/mlir-20.1.8/bin/mlir-opt"
    out = workspace / "artifacts/logs/mlir-docs" / datetime.now().strftime("%Y-%m-%d-passes")
    out.mkdir(parents=True, exist_ok=True)
    content = page.read_text()
    examples = {spec.strip(): code for kind, spec, code in EXAMPLE.findall(content)
                if kind == "example"}
    required = {"passes-base", "passes-cse-output", "passes-canonical-output", "passes-nested"}
    if not required.issubset(examples):
        raise SystemExit(f"Missing examples: {required - examples.keys()}")
    for name, code in examples.items():
        (out / f"{name}.mlir").write_text(code + "\n")
    checks = []

    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})

    def run(name, source, *flags, expected_exit=0):
        command = [str(opt), str(source), *flags]
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        (out / f"{name}.stdout.mlir").write_text(result.stdout)
        (out / f"{name}.stderr.txt").write_text(result.stderr)
        checks.append({"name": name, "command": command, "exit_code": result.returncode,
                       "passed": result.returncode == expected_exit})
        return result

    def pipeline(name, source, text, *flags, expected_exit=0):
        return run(name, source, "--pass-pipeline=" + text,
                   *flags, expected_exit=expected_exit)

    for name in examples:
        source = out / f"{name}.mlir"
        run(name + "-verify", source)
        run(name + "-generic", source, "--mlir-print-op-generic")
        run(name + "-roundtrip", out / f"{name}-generic.stdout.mlir")

    base, nested = out / "passes-base.mlir", out / "passes-nested.mlir"
    expected = examples["passes-canonical-output"].strip()
    cse = pipeline("cse", base, "builtin.module(func.func(cse))")
    check("displayed-cse-output", cse.stdout.strip() == examples["passes-cse-output"].strip())
    for name, text in [
        ("canonical", "builtin.module(func.func(canonicalize))"),
        ("cse-canonical", "builtin.module(func.func(cse,canonicalize))"),
        ("canonical-cse", "builtin.module(func.func(canonicalize,cse))"),
        ("configured", "builtin.module(func.func(canonicalize{max-iterations=4},cse))"),
    ]:
        result = pipeline(name, base, text)
        check(name + "-expected-output", result.stdout.strip() == expected)
    unchanged = pipeline("no-change-success", out / "passes-canonical-output.mlir",
                         "builtin.module(func.func(cse))")
    check("no-change-output", unchanged.stdout.strip() == expected)

    def additions(ir):
        bodies = re.findall(r"func\.func @(\w+)[^{]*\{(.*?)^\s*\}", ir, re.M | re.S)
        return {name: body.count("arith.addi") for name, body in bodies}

    direct = pipeline("direct", nested, "builtin.module(func.func(cse,canonicalize))",
                      "--mlir-disable-threading", "--mlir-print-ir-before-all",
                      "--mlir-print-ir-after-all")
    check("direct-functions-only", additions(direct.stdout) == {"f": 1, "g": 1, "h": 3})
    sequence = re.findall(r"IR Dump Before [^(]+\(([^)]+)\)[^\n]*\nfunc.func @(\w+)",
                          direct.stderr)
    check("serial-per-function-order", sequence == [
        ("cse", "f"), ("canonicalize", "f"), ("cse", "g"), ("canonicalize", "g")])
    inner = pipeline("inner", nested,
                     "builtin.module(builtin.module(func.func(cse,canonicalize)))")
    check("inner-functions-only", additions(inner.stdout) == {"f": 3, "g": 3, "h": 1})
    for name, text in [
        ("all-paths", "builtin.module(func.func(cse,canonicalize),builtin.module(func.func(cse,canonicalize)))"),
        ("module-scope", "builtin.module(cse,canonicalize)"),
    ]:
        result = pipeline(name, nested, text)
        check(name + "-all-simplified", additions(result.stdout) == {"f": 1, "g": 1, "h": 1})
    bad = pipeline("bad-anchor", base,
                   "builtin.module(func.func(convert-func-to-llvm))", expected_exit=1)
    check("anchor-diagnostic", "restricted to 'builtin.module'" in bad.stderr and
          "intended to run on 'func.func'" in bad.stderr)
    fail = pipeline("explicit-failure", base,
                    "builtin.module(func.func(canonicalize{max-iterations=1 test-convergence=true},cse))",
                    "--mlir-disable-threading", "--mlir-print-ir-before-all",
                    "--mlir-print-ir-after-failure", expected_exit=1)
    check("failure-dump", "IR Dump After Canonicalizer Failed" in fail.stderr)
    check("following-cse-not-started", "IR Dump Before CSE" not in fail.stderr)
    failed_ir = fail.stderr.split("IR Dump After Canonicalizer Failed", 1)[-1]
    check("failure-can-leave-modified-ir", additions(failed_ir) == {"twice": 1})

    manifest = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "page": str(page), "page_sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
        "version": subprocess.check_output([str(opt), "--version"], text=True).strip(),
        "machine_code_execution": False, "cpp_standalone_build": False,
        "passed": all(c["passed"] for c in checks), "checks": checks,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Pass chapter: {sum(c['passed'] for c in checks)}/{len(checks)} checks passed")
    print(f"Manifest: {out / 'manifest.json'}")
    for c in checks:
        if not c["passed"]:
            print("FAILED:", c["name"])
    return 0 if manifest["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
