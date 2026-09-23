#!/usr/bin/env python3
"""Compile and check the compiler-side examples in compiler/transforms/ir_api.md."""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import textwrap

from validate_examples import EXAMPLE


def main():
    workspace = Path(__file__).resolve().parents[3]
    page = workspace / "blog/docs/notes/compile/mlir/compiler/transforms/ir_api.md"
    project = Path(__file__).resolve().parent / "ir_api"
    llvm_build = workspace / "artifacts/builds/mlir-20.1.8"
    build = workspace / "artifacts/builds/mlir-ir-api-docs"
    out = workspace / "artifacts/logs/mlir-docs" / datetime.now().strftime("%Y-%m-%d-ir-api")
    out.mkdir(parents=True, exist_ok=True)
    content = page.read_text()
    checks = []

    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})

    def run(name, command, expected=0, timeout=30):
        result = subprocess.run([str(x) for x in command], capture_output=True,
                                text=True, timeout=timeout)
        (out / f"{name}.stdout.txt").write_text(result.stdout)
        (out / f"{name}.stderr.txt").write_text(result.stderr)
        checks.append({"name": name, "command": [str(x) for x in command],
                       "exit_code": result.returncode, "passed": result.returncode == expected})
        return result

    configure = run("configure", ["cmake", "-S", project, "-B", build, "-G", "Ninja",
        f"-DMLIR_DIR={llvm_build}/lib/cmake/mlir",
        f"-DLLVM_DIR={llvm_build}/lib/cmake/llvm", "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_CXX_COMPILER=/usr/bin/clang++", "-DCMAKE_C_COMPILER=/usr/bin/clang"], timeout=120)
    if configure.returncode:
        raise SystemExit(f"Configure failed; see {out}")
    compiled = run("build", ["cmake", "--build", build, "-j", "2"], timeout=240)
    if compiled.returncode:
        raise SystemExit(f"Build failed; see {out}")

    source = (project / "ir_api_demo.cpp").read_text()
    regions = {name: textwrap.dedent(code).strip() for name, code in re.findall(
        r"// BEGIN: ([\w-]+)\n(.*?)\s*// END: \1", source, re.S)}
    snippets = re.findall(r"<!-- cpp-example: ([\w-]+) -->\s*```cpp\n(.*?)\n```", content, re.S)
    check("all-source-regions-documented", {name for name, _ in snippets} == set(regions))
    for name, code in snippets:
        check("compiled-snippet-" + name, code.strip() == regions.get(name))

    examples = {spec.strip(): code for kind, spec, code in EXAMPLE.findall(content)
                if kind == "example"}
    required = {"ir-api-input", "ir-api-zero-output", "ir-api-rewrite-output"}
    if set(examples) != required:
        raise SystemExit(f"Expected examples {required}; got {set(examples)}")
    opt, exe = llvm_build / "bin/mlir-opt", build / "ir-api-demo"
    version = run("mlir-version", [opt, "--version"]).stdout
    normalized = {}
    for name, code in examples.items():
        path = out / f"{name}.mlir"
        path.write_text(code + "\n")
        normalized[name] = run(name + "-verify", [opt, path]).stdout.strip()
        generic = run(name + "-generic", [opt, path, "--mlir-print-op-generic"])
        generic_path = out / f"{name}-generic.mlir"
        generic_path.write_text(generic.stdout)
        run(name + "-roundtrip", [opt, generic_path])

    base = out / "ir-api-input.mlir"
    results = {}
    for mode in ["inspect", "zero", "rewrite", "build", "clone"]:
        result = run(mode, [exe, mode, base])
        results[mode] = result
        path = out / f"{mode}.mlir"
        path.write_text(result.stdout)
        run(mode + "-output-verify", [opt, path])
    for mode, target in [("inspect", "ir-api-input"), ("zero", "ir-api-zero-output"),
                         ("rewrite", "ir-api-rewrite-output")]:
        check(mode + "-displayed-output", results[mode].stdout.strip() == normalized[target])
    check("argument-not-op-result", "argument_has_defining_op=0" in results["inspect"].stderr)
    check("input-two-distinct-users", "x_uses=2 x_unique_users=2" in results["inspect"].stderr)
    after_zero = run("inspect-after-zero", [exe, "inspect", out / "zero.mlir"])
    check("two-uses-one-user", "x_uses=2 x_unique_users=1" in after_zero.stderr)
    repeat = run("rewrite-again", [exe, "rewrite", out / "rewrite.mlir"])
    check("rewrite-stable", repeat.stdout == results["rewrite"].stdout)

    trace = run("trace-one", [exe, "trace-one", base])
    trace_path = out / "trace-one.mlir"
    trace_path.write_text(trace.stdout)
    run("trace-one-output-verify", [opt, trace_path])
    phases = re.split(r"\n\[(?:before|after-rauw: old operation still exists|after-erase)\]\n",
                      trace.stderr)[1:]
    check("trace-three-phases", len(phases) == 3)
    if len(phases) == 3:
        check("trace-use-transfer", "old_uses=1\nreplacement_uses=2" in phases[0]
              and "old_uses=0\nreplacement_uses=3" in phases[1]
              and "replacement_uses=2" in phases[2] and "old_uses=" not in phases[2])
        check("trace-erase-separate-from-rauw",
              [phase.count(" = arith.addi ") for phase in phases] == [3, 3, 2])
    check("trace-only-one-add-removed", trace.stdout.count(" = arith.addi ") == 2)

    # Compare complete printed function bodies, so cloning must retain the
    # original's computation while the verifier checks its local SSA scope.
    def functions(ir):
        return dict(re.findall(r"func.func @(\w+)(\([^\n]*\{\n.*?^  \})", ir, re.M | re.S))

    original = functions(results["inspect"].stdout)["twice"]
    cloned = functions(results["clone"].stdout)
    check("clone-preserves-original-and-body", set(cloned) == {"twice", "twice_copy"}
          and cloned["twice"] == original and cloned["twice_copy"] == original)
    built = functions(results["build"].stdout)
    canonical_sum = functions(normalized["ir-api-zero-output"])["twice"]
    canonical_sum = "\n".join(line for line in canonical_sum.splitlines()
                               if "arith.constant" not in line)
    check("constructed-function-body", set(built) == {"twice", "twice_built"}
          and built["twice"] == original and built["twice_built"] == canonical_sum)

    # Check that the deliberately restricted rewrite leaves nearby inputs
    # alone. These are semantic boundaries, not additional supported rules.
    fixtures = {
        "nonzero": "%c = arith.constant 1 : i32\n%r = arith.addi %x, %c : i32\nreturn %r : i32",
        "zero-on-left": "%c = arith.constant 0 : i32\n%r = arith.addi %c, %x : i32\nreturn %r : i32",
        "overflow-flags": "%r = arith.addi %x, %x overflow<nsw> : i32\nreturn %r : i32",
        "wide-type": "%w = arith.extsi %x : i32 to i64\n%r = arith.addi %w, %w : i64\nreturn %x : i32",
    }
    for name, body in fixtures.items():
        path = out / f"{name}.mlir"
        path.write_text("module {\nfunc.func @twice(%x: i32) -> i32 {\n" + body + "\n}\n}\n")
        before = run(name + "-input-verify", [opt, path])
        after = run(name + "-rewrite", [exe, "rewrite", path])
        check(name + "-not-matched", before.stdout == after.stdout)

    for mode, diagnostic in [("bad-dominance", "operand #1 does not dominate this use"),
                             ("bad-clone", "using value defined outside the region")]:
        result = run(mode, [exe, mode, base], expected=2)
        check(mode + "-expected-diagnostic", diagnostic in result.stderr)
        check(mode + "-modified-ir-dump", "IR after failed verification:" in result.stderr)

    manifest = {"date": datetime.now().isoformat(), "llvm_version": version,
                "files_sha256": {str(path.relative_to(workspace)):
                    hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in [page, project / "ir_api_demo.cpp", project / "CMakeLists.txt",
                                 Path(__file__).resolve()]}, "checks": checks}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    failed = [item["name"] for item in checks if not item["passed"]]
    print(f"{len(checks) - len(failed)}/{len(checks)} checks passed; {out / 'manifest.json'}")
    if failed:
        raise SystemExit("Failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
