#!/usr/bin/env python3
"""Build the worked example and show the actual IR before and after its Pass."""
import argparse
from datetime import datetime
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="MLIR input; defaults to input.mlir")
    parser.add_argument("--test", action="store_true", help="also run lit/FileCheck")
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    workspace = project.parents[2]
    build = workspace / "artifacts/builds/mlir-small-pass"
    llvm = workspace / "artifacts/builds/mlir-20.1.8"
    out = workspace / "artifacts/logs/mlir-small-pass" / datetime.now().strftime("%Y-%m-%d-%H%M%S-%f")
    out.mkdir(parents=True)

    def run(name, cmd, show=False):
        result = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, timeout=240)
        (out / f"{name}.stdout.txt").write_text(result.stdout)
        (out / f"{name}.stderr.txt").write_text(result.stderr)
        if show or result.returncode:
            print(result.stdout, end="")
            print(result.stderr, end="")
        if result.returncode:
            raise SystemExit(f"{name} failed ({result.returncode}); logs: {out}")
        return result.stdout

    print("构建 lab-opt（复用工作区 MLIR 20.1.8）", flush=True)
    run("configure", ["cmake", "-S", project, "-B", build, "-G", "Ninja",
        f"-DMLIR_DIR={llvm}/lib/cmake/mlir", f"-DLLVM_DIR={llvm}/lib/cmake/llvm",
        "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=/usr/bin/clang++",
        "-DCMAKE_C_COMPILER=/usr/bin/clang"])
    run("build", ["cmake", "--build", build, "-j", "2"])
    input_path = (args.input or project / "input.mlir").resolve()
    pipeline = "builtin.module(func.func(lab-remove-add-zero))"
    print("\n修改前（解析并打印）：", flush=True)
    before = run("before", [build / "lab-opt", input_path], show=True)
    print(f"\n运行 pipeline：{pipeline}\n修改后：", flush=True)
    after = run("after", [build / "lab-opt", input_path, "--pass-pipeline=" + pipeline, "--verify-each"], show=True)
    (out / "before.mlir").write_text(before)
    (out / "after.mlir").write_text(after)
    print("\n观察：哪些 use 被接回函数参数？加法与零常量分别由谁删除？")
    if args.test:
        print("\n运行 lit / FileCheck：", flush=True)
        run("lit", [llvm / "bin/llvm-lit", "-v", project / "tests"], show=True)
    print(f"\n本次输入输出与日志：{out}")


if __name__ == "__main__":
    main()
