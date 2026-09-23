#!/usr/bin/env python3
"""Show ODS-generated operation parsing, printing, construction and expansion."""
import argparse
from datetime import datetime
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    workspace = project.parents[2]
    build = workspace / "artifacts/builds/mlir-op-definition"
    llvm = workspace / "artifacts/builds/mlir-20.1.8"
    out = workspace / "artifacts/logs/mlir-op-definition" / datetime.now().strftime("%Y-%m-%d-%H%M%S-%f")
    out.mkdir(parents=True)

    def run(name, command, expected=0, show=True):
        result = subprocess.run([str(x) for x in command], capture_output=True, text=True, timeout=240)
        (out / (name + ".stdout.txt")).write_text(result.stdout)
        (out / (name + ".stderr.txt")).write_text(result.stderr)
        if show or result.returncode != expected:
            print(result.stdout, end="")
            print(result.stderr, end="")
        if result.returncode != expected:
            raise SystemExit(f"{name} failed: {out}")
        return result

    print("生成 ODS C++ 并构建工具", flush=True)
    run("configure", ["cmake", "-S", project, "-B", build, "-G", "Ninja",
        f"-DMLIR_DIR={llvm}/lib/cmake/mlir", f"-DLLVM_DIR={llvm}/lib/cmake/llvm",
        "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=/usr/bin/clang++",
        "-DCMAKE_C_COMPILER=/usr/bin/clang"], show=False)
    run("build", ["cmake", "--build", build, "-j", "2"], show=False)
    opt = build / "lab-dialect-opt"
    path = (args.input or project / "input.mlir").resolve()
    print("\n1. 解析并验证，自定义格式：", flush=True)
    run("custom", [opt, path])
    print("\n2. 同一 IR 的通用格式：", flush=True)
    generic = run("generic", [opt, path, "--mlir-print-op-generic"])
    generic_path = out / "generic.mlir"
    generic_path.write_text(generic.stdout)
    run("roundtrip", [opt, generic_path], show=False)
    print("\n3. C++ builder 创建独立的 clip 函数：", flush=True)
    run("builder", [build / "lab-build"])
    print("\n4. Pass 展开为 arith：", flush=True)
    run("expanded", [opt, path, "--pass-pipeline=builtin.module(func.func(lab-expand-clamp))", "--verify-each"])
    print("\n5. builder 能构造上下界颠倒的对象；显式验证拒绝它：", flush=True)
    invalid = run("invalid-builder", [build / "lab-build", "invalid"], expected=1, show=False)
    print(invalid.stderr, end="")
    if args.test:
        print("\n运行 lit 正反例：", flush=True)
        run("lit", [llvm / "bin/llvm-lit", "-v", project / "tests"])
    print(f"\n生成源码：{build}/LabOps.h.inc 与 LabOps.cpp.inc")
    print(f"本次观察记录：{out}")


if __name__ == "__main__":
    main()
