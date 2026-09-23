#!/usr/bin/env python3
"""Show real compiler-side IR changes, one learning step at a time."""

import argparse
from datetime import datetime
import difflib
import json
from pathlib import Path
import shlex
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", choices=["rauw", "rewrite", "dominance", "clone"],
                        default="rauw", help="默认只观察一次 RAUW 与 erase")
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("twice.mlir"))
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parents[3]
    source = args.input.resolve()
    if not source.is_file():
        parser.error(f"输入文件不存在：{source}")
    out = workspace / "artifacts/logs/mlir-labs" / datetime.now().strftime("%Y-%m-%d-%H%M%S-%f-ir-api")
    out.mkdir(parents=True)
    project = workspace / "aicompiler-labs/llvm-mlir/docs/ir_api"
    llvm_build = workspace / "artifacts/builds/mlir-20.1.8"
    build = workspace / "artifacts/builds/mlir-ir-api-docs"
    exe = build / "ir-api-demo"
    commands = []

    def run(name, command, expected=0):
        result = subprocess.run([str(x) for x in command], capture_output=True,
                                text=True, timeout=240)
        (out / f"{name}.stdout.txt").write_text(result.stdout)
        (out / f"{name}.stderr.txt").write_text(result.stderr)
        commands.append({"command": [str(x) for x in command], "exit_code": result.returncode})
        (out / "commands.json").write_text(json.dumps(commands, indent=2, ensure_ascii=False) + "\n")
        if result.returncode != expected:
            print(result.stderr or result.stdout)
            raise SystemExit(f"{name} 返回 {result.returncode}，预期 {expected}；日志：{out}")
        return result

    print("准备 C++ 观察工具（增量构建）；完整构建日志保存在本次输出目录。", flush=True)
    run("configure", ["cmake", "-S", project, "-B", build, "-G", "Ninja",
        f"-DMLIR_DIR={llvm_build}/lib/cmake/mlir", f"-DLLVM_DIR={llvm_build}/lib/cmake/llvm",
        "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=/usr/bin/clang++",
        "-DCMAKE_C_COMPILER=/usr/bin/clang"])
    run("build", ["cmake", "--build", build, "-j", "2"])
    # Preserve the learner's exact input and use a stable copy for this run.
    snapshot = out / "input.mlir"
    snapshot.write_bytes(source.read_bytes())
    opt = llvm_build / "bin/mlir-opt"
    before = run("input-verify", [opt, snapshot]).stdout
    (out / "before.mlir").write_text(before)

    def demo(mode, input_path=snapshot, expected=0):
        print("\n执行：" + shlex.join([str(exe.relative_to(workspace)), mode,
                                        str(input_path.relative_to(workspace))]))
        label = f"{len(commands):02d}-{mode}"
        result = run(label, [exe, mode, input_path], expected)
        if result.stdout:
            (out / f"{mode}.mlir").write_text(result.stdout)
            run(label + "-verify", [opt, out / f"{mode}.mlir"])
        return result

    def compare(previous, result, title):
        print("\n" + title + "\n" + result.stdout)
        print("差异（- 为原行，+ 为新行；SSA 打印编号可能变化）：")
        diff = "".join(difflib.unified_diff(previous.splitlines(True),
                                           result.stdout.splitlines(True),
                                           fromfile="before", tofile="after"))
        print(diff or "没有变化：检查输入是否满足这条规则的匹配条件。")
        if result.stderr:
            print("观察信息：\n" + result.stderr)

    if args.step == "rauw":
        print("\n观察目标：只处理第一条匹配的 x+0，分开看 RAUW 和 erase。")
        print("先关注 old_uses 与 replacement_uses，再看哪个 operand 改变了来源。")
        result = demo("trace-one")
        print(result.stderr)
        print("after-rauw 中旧加法仍在，原先的 use 已转接；after-erase 才删除旧操作。")
        print("replacement_uses 在 erase 后还可能减少：旧加法原本也使用了 replacement。")
    elif args.step == "rewrite":
        print("\n原始 IR：\n" + before)
        initial = demo("inspect")
        print("原始参数的使用关系：\n" + initial.stderr)
        zero = demo("zero")
        compare(before, zero, "消除加零之后（常量尚未清理）：")
        info = demo("inspect", out / "zero.mlir")
        print("简化后参数的使用关系：\n" + info.stderr)
        rewritten = demo("rewrite", out / "zero.mlir")
        compare(zero.stdout, rewritten, "创建乘法、替换旧结果并清理之后：")
    elif args.step == "dominance":
        print("\n原始 IR：\n" + before)
        correct = demo("rewrite")
        compare(before, correct, "合法插入位置：")
        bad = demo("bad-dominance", expected=2)
        if "operand #1 does not dominate this use" not in bad.stderr:
            raise SystemExit(f"未得到本节预期的支配错误，请检查输入。日志：{out}")
        print("故意把常量放得太晚，verifier 拒绝了修改后的 IR：\n" + bad.stderr)
        print("对照乘法与常量的顺序：类型相同仍不足以保证输入可用。")
    else:
        print("\n原始 IR：\n" + before)
        correct = demo("clone")
        compare(before, correct, "有参数映射的克隆：")
        bad = demo("bad-clone", expected=2)
        if "using value defined outside the region" not in bad.stderr:
            raise SystemExit(f"未得到本节预期的隔离错误，请检查输入。日志：{out}")
        print("省略参数映射，verifier 拒绝了新函数对旧函数参数的引用：\n" + bad.stderr)
        print("比较两份函数的入口参数归属，不能只比较打印出来的名字。")
    print(f"\n本次原始输入、输出、诊断和命令：{out}")
    print("这些输出来自实际 C++ IR 操作；尚未执行生成函数的机器码。")


if __name__ == "__main__":
    main()
