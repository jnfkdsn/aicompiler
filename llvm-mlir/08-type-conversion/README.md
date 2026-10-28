# 类型转换与边界实验

本实验沿 `my.limit → arith` 观察 range 到 i32 的转换，连接生产者、函数、调用与 Region 的入口/出口。方言定义直接复用 `06-ir-definition`；07 实验继续承担无类型变化的操作合法性主题，两者独立构建。

正文在 blog 中独立讲解，本目录用于实际观察、改动与验证：

- [类型转换与函数签名](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/compiler/conversion/type_conversion.md)
- [混合表示与边界衔接](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/compiler/conversion/materialization.md)
- [调用与区域边界](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/compiler/conversion/boundaries.md)
- [复杂转换路径与框架行为](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/compiler/conversion/advanced.md)

以上使用 blog 仓库的文件地址；两仓库各自提交后才能在线访问新增内容，不依赖工作区的相对路径。

## 构建与直接运行

在 workspace 根目录执行，工具链为固定的 LLVM 20.1.8：

```bash
cmake -S aicompiler-labs/llvm-mlir/08-type-conversion \
  -B artifacts/builds/mlir-type-conversion -G Ninja \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DLLVM_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/llvm" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=/usr/bin/clang \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++
cmake --build artifacts/builds/mlir-type-conversion -j2
artifacts/builds/mlir-type-conversion/range-opt \
  aicompiler-labs/llvm-mlir/08-type-conversion/limit.mlir \
  --pass-pipeline='builtin.module(my-convert-range)' --verify-each
```

`limit.mlir` 的结果应是 i32 函数，内部有两条常量、maxsi、minsi 与 return，不再有 range 或 limit。这个 Pass 在模块层运行，以便协调函数定义和调用。

## 逐项观察

`range-probe` 直接接收模式和输入文件，不用每次修改 Pass 来制造失败。先阅读输入，预测改变的位置，再运行：

```bash
artifacts/builds/mlir-type-conversion/range-probe partial \
  aicompiler-labs/llvm-mlir/08-type-conversion/limit.mlir
artifacts/builds/mlir-type-conversion/range-probe no-call \
  aicompiler-labs/llvm-mlir/08-type-conversion/calls.mlir
```

| 模式与输入 | 预期 | 应观察的位置 |
|---|---|---|
| `full limit.mlir` | 成功 | limit 结果、return 与函数返回类型一起变化 |
| `full-no-bridge limit.mlir` | 成功 | 相关使用者全部转换，不需要遗留桥接 |
| `partial limit.mlir` | 成功 | 函数仍返回 range，minsi 后出现一个 source cast |
| `partial-no-bridge limit.mlir` | 失败，exit 1 | 缺少仍被 return 使用的 materialization |
| `full calls.mlir` | 成功 | 函数签名、call 输入/结果、return 一致 |
| `no-call calls.mlir` | 失败，exit 1 | 只漏掉 func.call 的转换规则 |
| `full scope.mlir` | 成功 | 父操作、Block 参数、yield 与外部 return 一致 |
| `no-yield scope.mlir` | 失败，exit 1 | 只漏掉区域出口规则 |
| `full branch.mlir` | 成功 | cf.br 实参与目标 Block 参数同步 |
| `analysis analysis-mixed.mlir` | 成功 | stderr 报告 limit 可合法化；打印的输入保持原样 |
| `full analysis-mixed.mlir` | 失败，exit 1 | 未提供规则的 my.clamp 不满足 full 目标 |
| `recursive limit.mlir` | 成功 | 函数内部被递归合法性跳过，limit 保留 |

普通解析/verifier 失败用 exit 2，与 conversion 失败区分。除表中输入外，这些模式并不承诺能处理任意 My 操作或任意类型组合。

保存 partial 输出后，用 `finish` 对该文件继续转换并检查没有剩余 cast。`full` 的阶段目标允许占位 cast；`finish` 额外拒绝无法消解的 cast。单独清理可使用：

```bash
artifacts/builds/mlir-type-conversion/range-opt \
  aicompiler-labs/llvm-mlir/08-type-conversion/cast-roundtrip.mlir \
  --reconcile-unrealized-casts
```

这能消去示例中的往返关系，但不能仅靠清理改变 partial 输出的旧函数接口。全部观察（打印输入、完整命令、输出、诊断和退出码）可一次运行：

```bash
python3 aicompiler-labs/llvm-mlir/08-type-conversion/observe.py
```

日志保存在 `artifacts/logs/mlir-type-conversion/`，源码与原始生成物分开存放。

## 源码位置

| 文件 | 负责的工作 |
|---|---|
| `RangeConversion.cpp` | TypeConverter、limit/scope/yield 规则、动态目标、标准函数/调用/分支规则、Pass |
| `RangeConversion.h` | 对照模式的选项与转换入口 |
| `range-opt.cpp` | 注册方言、Pass 和标准 cast 清理工具入口 |
| `range-probe.cpp` | 选择对照模式，区分验证/转换失败并打印结果 |
| `*.mlir` | 博客输入、调用/区域/分支、analysis 与 cast 对照 |

## 阅读后任选一个改动

1. **边界值**：复制 `limit.mlir`，将 bounds 属性和 range 类型同时改为 `[7,7]`。先推导数值，再观察常量和 max/min；只修改其中一处时，应在源 verifier 阶段失败。
2. **新输入**：不修改规则，自己写一个 scope 输入，传入两个不同 range 值，以反向顺序 yield。逐项标注 operand、Block 参数、yield、结果与 return 的对应，再检查转换后位置仍一致。可以先用相同 range 简化语法，再使用不同区间强化检查。
3. **规则实现**：复制工程到个人练习目录，暂时移除 `ConvertYield`，观察 `no-yield` 对照，然后独立补回出口转换。目标是解释为何必须使用转换后的输入，不只是抄回函数名。

完成一项即可提交输入、改动、输出和解释，不要求一次做完全部任务。作者已经完成参考实现与验证，不代表学习者已独立实践。

## 验证范围

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_type_conversion.py
```

检查正文/源码片段一致、输入与打印往返、完整输出、缺失桥接/规则诊断、零/多结果及嵌套 Region、边界常量、analysis 与递归合法性、cast 清理与最终残留检查。报告保存到 `artifacts/logs/mlir-docs/`。

这些是编译器侧结构、类型、引用和合法化测试。本实验没有执行转换后程序的数值测试；scope 仍留在结果中，后续需要实现执行路径。占位 cast 不进行范围检查，不是任意 i32 到 range 的运行时转换。range 参数降低成 i32 后，原调用前提仍需由调用方或后续显式检查维护。
