#!/usr/bin/env python3
"""Verify the compiled examples in the rewriting and rewrite_drivers chapters."""

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
    pages = [workspace / "blog/docs/notes/compile/mlir/compiler/transforms" / name
             for name in ("rewriting.md", "rewrite_drivers.md")]
    project = Path(__file__).resolve().parent / "rewriting"
    llvm_build = workspace / "artifacts/builds/mlir-20.1.8"
    build = workspace / "artifacts/builds/mlir-rewriting-docs"
    out = workspace / "artifacts/logs/mlir-docs" / datetime.now().strftime("%Y-%m-%d-rewriting")
    out.mkdir(parents=True, exist_ok=True)
    checks = []

    def check(name, condition):
        checks.append({"name": name, "passed": bool(condition)})

    def run(name, command, expected=0, timeout=30):
        result = subprocess.run([str(x) for x in command], capture_output=True,
                                text=True, timeout=timeout)
        (out / f"{name}.stdout.txt").write_text(result.stdout)
        (out / f"{name}.stderr.txt").write_text(result.stderr)
        checks.append({"name": name, "command": [str(x) for x in command],
                       "exit_code": result.returncode, "passed": result.returncode == expected})
        return result

    conf = run("configure", ["cmake", "-S", project, "-B", build, "-G", "Ninja",
        f"-DMLIR_DIR={llvm_build}/lib/cmake/mlir", f"-DLLVM_DIR={llvm_build}/lib/cmake/llvm",
        "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=/usr/bin/clang++",
        "-DCMAKE_C_COMPILER=/usr/bin/clang"], timeout=120)
    if conf.returncode:
        raise SystemExit(f"Configure failed: {out}")
    compiled = run("build", ["cmake", "--build", build, "-j", "2"], timeout=240)
    if compiled.returncode:
        raise SystemExit(f"Build failed: {out}")
    content = "\n".join(page.read_text() for page in pages)
    source = (project / "rewriting_demo.cpp").read_text()
    regions = {name: textwrap.dedent(code).strip() for name, code in re.findall(
        r"// BEGIN: ([\w-]+)\n(.*?)\s*// END: \1", source, re.S)}
    snippets = re.findall(r"<!-- cpp-example: ([\w-]+) -->\s*```cpp\n(.*?)\n```", content, re.S)
    check("all-compiled-regions-documented", set(regions) == {name for name, _ in snippets})
    check("unique-compiled-snippets", len(snippets) == len(regions))
    for name, code in snippets:
        check("compiled-snippet-" + name, regions.get(name) == code.strip())
    examples = {spec.strip(): code for kind, spec, code in EXAMPLE.findall(content)
                if kind == "example"}
    required = {"rewriting-input", "rewriting-greedy-output", "rewriting-walk-output",
                "rewriting-fold-output", "rewriting-double-input", "rewriting-left-zero",
                "rewriting-single-input", "rewriting-single-output"}
    if set(examples) != required:
        raise SystemExit("Unexpected document examples")
    opt, exe = llvm_build / "bin/mlir-opt", build / "rewriting-demo"
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

    def demo(name, mode, path, expected=0):
        result = run(name, [exe, mode, path], expected)
        output = out / f"{name}.mlir"
        output.write_text(result.stdout)
        run(name + "-output-verify", [opt, output])
        return result

    base = out / "rewriting-input.mlir"
    greedy = demo("greedy", "greedy", base)
    walk = demo("walk", "walk", base)
    empty = demo("empty", "empty", base)
    fold = demo("fold-only", "fold-only", base)
    for name, result, target in [
        ("greedy", greedy, "rewriting-greedy-output"),
        ("walk", walk, "rewriting-walk-output"),
        ("empty", empty, "rewriting-input"),
        ("fold-only", fold, "rewriting-fold-output"),
    ]:
        check(name + "-displayed-output", result.stdout.strip() == normalized[target])
    actions = lambda result: re.findall(r"^APPLY (\w+)$", result.stderr, re.M)
    single = demo("single", "single", out / "rewriting-single-input.mlir")
    check("single-displayed-output", single.stdout.strip() == normalized["rewriting-single-output"])
    check("single-success-trace", actions(single) == ["RemoveAddZero"])
    nonzero = out / "single-nonzero.mlir"
    nonzero.write_text(examples["rewriting-single-input"].replace("arith.constant 0", "arith.constant 1"))
    before = run("single-nonzero-input-verify", [opt, nonzero])
    after = demo("single-nonzero", "single", nonzero)
    check("single-exercise-no-mutation", before.stdout == after.stdout and not actions(after))
    check("greedy-success-trace", actions(greedy) == [
        "RemoveAddZero", "RemoveAddZero", "DoubleToMul", "MulTwoToShift"])
    check("walk-stops-before-new-mul", actions(walk) == [
        "RemoveAddZero", "RemoveAddZero", "DoubleToMul"])
    check("fold-without-custom-pattern", not actions(fold) and "converged=1 changed=1" in fold.stderr)
    check("success-without-change", "converged=1 changed=0" in empty.stderr)
    repeat = demo("repeat", "greedy", out / "greedy.mlir")
    check("greedy-fixed-point", repeat.stdout == greedy.stdout and not actions(repeat)
          and "converged=1 changed=0" in repeat.stderr)
    resumed = demo("greedy-after-walk", "greedy", out / "walk.mlir")
    check("new-op-processed-on-resume", resumed.stdout == greedy.stdout
          and actions(resumed) == ["MulTwoToShift"])

    double = out / "rewriting-double-input.mlir"
    for mode, chosen, rejected in [("prefer-mul", "DoubleToMul", "DoubleToShift"),
                                    ("prefer-shift", "DoubleToShift", "DoubleToMul")]:
        result = demo(mode, mode, double)
        check(mode + "-candidate-choice", actions(result) == [chosen] and rejected not in actions(result))
        check(mode + "-output", ("arith.muli" if mode == "prefer-mul" else "arith.shli") in result.stdout)
    inplace = demo("in-place", "in-place", out / "rewriting-left-zero.mlir")
    check("inplace-revisited", actions(inplace) == ["MoveZeroToRhs", "RemoveAddZero"]
          and "return %arg0 : i32" in inplace.stdout and "arith." not in inplace.stdout)
    cycle = demo("cycle", "cycle", double, expected=2)
    check("cycle-limited-not-rolled-back", "converged=0 changed=1" in cycle.stderr
          and actions(cycle) == ["DoubleToMul", "MulTwoToDouble"] * 4
          and "arith.constant" in cycle.stdout)

    fixtures = {
        "nonzero": "func.func @twice(%x:i32)->i32 {%c=arith.constant 1:i32 %r=arith.addi %x,%c:i32 return %r:i32}",
        "different-values": "func.func @twice(%x:i32,%y:i32)->i32 {%r=arith.addi %x,%y:i32 return %r:i32}",
        "flags": "func.func @twice(%x:i32)->i32 {%r=arith.addi %x,%x overflow<nsw>:i32 return %r:i32}",
        "wide": "func.func @twice(%x:i64)->i64 {%r=arith.addi %x,%x:i64 return %r:i64}",
    }
    for name, body in fixtures.items():
        path = out / f"{name}.mlir"
        path.write_text("module {" + body + "}\n")
        before = run(name + "-input-verify", [opt, path])
        after = demo(name + "-greedy", "greedy", path)
        check(name + "-reject-without-mutation", before.stdout == after.stdout
              and not actions(after) and "converged=1 changed=0" in after.stderr)
    dead = out / "dead.mlir"
    dead.write_text("module {func.func @twice(%x:i32)->i32 {%r=arith.addi %x,%x:i32 return %x:i32}}\n")
    run("dead-input-verify", [opt, dead])
    cleaned = demo("dead-empty-rules", "empty", dead)
    check("dce-even-with-fold-disabled", "arith.addi" not in cleaned.stdout and not actions(cleaned)
          and "converged=1 changed=1" in cleaned.stderr)

    files = [*pages, project / "rewriting_demo.cpp", project / "CMakeLists.txt", Path(__file__).resolve()]
    manifest = {"date": datetime.now().isoformat(), "llvm_version": version,
                "files_sha256": {str(p.relative_to(workspace)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in files}, "checks": checks}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    failures = [c["name"] for c in checks if not c["passed"]]
    print(f"{len(checks) - len(failures)}/{len(checks)} checks passed; {out / 'manifest.json'}")
    if failures:
        raise SystemExit("Failed: " + ", ".join(failures))


if __name__ == "__main__":
    main()
