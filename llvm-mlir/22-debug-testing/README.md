# 22：失败复现、缩减与回归

目标：把三个函数中的失败缩到一条带标记乘法，并确认缩减保留的是同一个原因。这个 Pass 人为拒绝 `my.trigger` 乘法，不代表上游 bug。

## 直接构建与观察

在 workspace 根目录：

```bash
cmake -G Ninja -S aicompiler-labs/llvm-mlir/22-debug-testing \
  -B artifacts/builds/mlir-debug-testing \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=/usr/bin/clang \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++
cmake --build artifacts/builds/mlir-debug-testing -j 2
artifacts/builds/mlir-debug-testing/my-opt \
  aicompiler-labs/llvm-mlir/22-debug-testing/input.mlir \
  --pass-pipeline='builtin.module(canonicalize,my-reject-marked-mul)' \
  --mlir-disable-threading --mlir-print-ir-before-all \
  --mlir-print-ir-after-failure
```

最后一条预期失败，诊断 `teaching restriction: marked multiply is unsupported`。先看 canonicalize 删除哪些内容，再确认失败仍由带标记乘法触发。

```bash
python3 aicompiler-labs/llvm-mlir/22-debug-testing/observe.py
python3 aicompiler-labs/llvm-mlir/docs/validate_debugging.py
```

observe 显示完整命令与结果，包括 local reproducer 保存/重放、mlir-reduce、Instrumentation、统计/时间、lit 和 LSP 握手。产物写入 artifacts/logs/mlir-docs/*-debug-testing；reproducer.mlir 保存失败前输入和 pipeline，reduced.mlir 只剩 hit 函数。

interesting.py 约定 1=interesting、0=不保留；只接受指定诊断，语法错误、超时及无法启动不算复现。统计与 timing 属于编译器，不是 kernel。LSP 只做 initialize/shutdown 协议检查；未做 IDE 配置或 GDB 会话。

CMake 匹配上游 assertions 配置：Statistic 的类型随配置改变，外部 Release 工程不能无条件保留 NDEBUG。LLVM 20.1.8 的固定源码与上游工具仍按 environments/version-matrix.md 配置。

## 有限练习

1. 复制 input.mlir，增加一个无关函数，预测 reducer 是否会保留它；检查缩减后的输入仍是合法 IR。
2. 在成功输出的副本中把 return 的乘法结果改为原参数，运行 tests/accept.mlir 的 FileCheck，解释为何失败。
3. 在自己的副本里让限制同时要求第二个属性，补成功与失败测试，避免把所有带标记操作都拒绝。

作者验证只说明参考工程已执行，不表示学习者已完成这些修改。
