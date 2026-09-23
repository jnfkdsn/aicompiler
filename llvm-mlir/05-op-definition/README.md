# 05：定义一个操作

正文：[一个操作是怎样被定义出来的](../../../blog/docs/notes/compile/mlir/compiler/ir_definition/op_definition.md)。沿 `lab.clamp` 观察语义约定、ODS、生成的访问器/builder、验证、注册、打印及 Pass 展开。这里是作者提供的完整示例，阅读后再做有限修改。

## 观察入口

workspace 根目录运行：

```bash
python3 aicompiler-labs/llvm-mlir/05-op-definition/observe.py --test
```

依次打印自定义格式、通用格式、C++ 构造结果、展开后的 IR，以及构造非法上下界后 verifier 的拒绝。`--input PATH` 只替换解析与展开的输入；builder 观察始终构造固定的独立示例。

默认复用 `artifacts/builds/mlir-20.1.8` 的 LLVM/MLIR 20.1.8、Clang 14 与 Ninja。构建在 `artifacts/builds/mlir-op-definition`，逐次日志在 `artifacts/logs/mlir-op-definition/<时间>`。本项目不修改 `04-small-pass` 或上游源码。

## 工程文件

| 文件 | 作用 |
|---|---|
| `LabOps.td` | Dialect/Op 的声明、静态约束与 assembly format |
| `LabOps.h` / `LabOps.cpp` | 引入生成代码、注册操作，手写上下界 verifier |
| `CMakeLists.txt` | 调用 mlir-tblgen，编译生成文件与手写实现 |
| `lab-dialect-opt.cpp` | 注册 Dialect 和展开 Pass，使用 MlirOptMain |
| `lab-build.cpp` | 经生成 builder 构造 Op，显式调用 verify |
| `ExpandClamp.cpp` | 将 clamp 展开为 signed max/min 的小 Pass |
| `tests/` | 解析/打印往返、生成约束与手写验证错误、builder、展开关系 |

生成的 `LabOps.h.inc` / `LabOps.cpp.inc` 与 `LabDialect.*.inc` 保存在 build 中。查源码时沿 `getInput`、`getLowerAttr`、`ClampOp::build`、`verifyInvariantsImpl`、`ClampOp::verifyInvariants` 定位，不编辑生成文件。

## 单独构建与运行

```bash
cmake -S aicompiler-labs/llvm-mlir/05-op-definition \
  -B artifacts/builds/mlir-op-definition -G Ninja \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DLLVM_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/llvm" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++ \
  -DCMAKE_C_COMPILER=/usr/bin/clang
cmake --build artifacts/builds/mlir-op-definition -j 2
artifacts/builds/mlir-op-definition/lab-dialect-opt aicompiler-labs/llvm-mlir/05-op-definition/input.mlir --mlir-print-op-generic
artifacts/builds/mlir-op-definition/lab-dialect-opt aicompiler-labs/llvm-mlir/05-op-definition/input.mlir --pass-pipeline='builtin.module(func.func(lab-expand-clamp))' --verify-each
artifacts/builds/mlir-20.1.8/bin/llvm-lit -v aicompiler-labs/llvm-mlir/05-op-definition/tests
```

对 `lab-build invalid`，预期退出码为 1，日志先显示 builder 完成，再显示上下界诊断。`--verify-diagnostics` 则检查预期诊断是否出现：非法输入按预期被拒绝时，这类测试整体成功。

测试包含负数边界、相等边界和 i32 完整范围；这些验证 IR 契约及展开关系，不是目标机器码的数值执行测试。Pass 使用普通 Pattern + Walk 展开，未实现 Dialect Conversion 的 legality/TypeConverter 协议。

## 阅读后的动手入口

观察完本工程后，进入 [练习 01：clamp 简化](../exercises/01-clamp-simplify/README.md)。任务单、独立工具外壳、输入与行为检查已经准备好，匹配/改写的 TODO 留给你实现。它复用本工程的 LabOps，不需要改动这里与正文对应的参考实现。

首次源码阅读可按 [验证与替换两条路线](../exercises/01-clamp-simplify/SOURCE_READING.md) 选择一条，连接本工程、生成代码与上游具体函数。完成判据和提交审阅方式均在任务 README 中。

文档维护检查：

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_op_definition.py
```

正文使用独立 `lab-example` 标记，由加载 Lab dialect 的工具验证。通用 `validate_examples.py` 继续负责标准方言示例。
