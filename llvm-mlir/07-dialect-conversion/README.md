# 07：操作转换与目标合法性

对应 blog 的 [Dialect Conversion：操作转换与目标合法性](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/compiler/conversion/operation_conversion.md)。原理正文独立展示转换过程；这里用于预测、运行并改变一个条件。

本工程复用 `05-op-definition` 的 MyOps 库，保持 `my.clamp` 定义不变，添加模块 Pass `my-clamp-to-arith`。不同时链接 06 的另一份方言定义。当前只处理操作转换，尚未加入 TypeConverter。

## 构建与第一次观察

从 workspace 根目录运行，使用已有 LLVM/MLIR 20.1.8 构建：

```bash
cmake -S aicompiler-labs/llvm-mlir/07-dialect-conversion \
  -B artifacts/builds/mlir-dialect-conversion -G Ninja \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DLLVM_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/llvm" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++ -DCMAKE_C_COMPILER=/usr/bin/clang
cmake --build artifacts/builds/mlir-dialect-conversion -j2

artifacts/builds/mlir-dialect-conversion/my-convert-opt \
  aicompiler-labs/llvm-mlir/07-dialect-conversion/input.mlir \
  --pass-pipeline='builtin.module(my-clamp-to-arith)' --verify-each
```

输入只有一条 clamp；输出包含两个 constant、一个 maxsi、一个 minsi，return 使用 minsi 的结果。只运行工具而不传 pipeline 时，clamp 仍会原样保留，说明输入本身能通过验证。

## 相同输入下改变目标和模式

观察工具 `conversion-probe MODE FILE` 与 Pass 共享目标和规则实现，以下模式每次独立解析输入：

| 模式 | 改变的条件 | 建议输入与预期 |
|---|---|---|
| `full` | 使用正常目标与展开规则 | input 成功；mixed 因 addi 未获许可而失败 |
| `partial` | 只更换转换模式 | mixed 成功，原有 addi 保留并接到新结果 |
| `full-no-rule` / `partial-no-rule` | 规则集合为空 | input 均失败，clamp 被明确标记为 illegal |
| `full-no-constant` / `partial-no-constant` | 目标漏掉 constant | input 均失败，规则新建的常量无法合法化 |
| `full-dynamic` / `partial-dynamic` | maxsi 只接受 i32 | input 成功；wide 中 i64 maxsi 被明确拒绝 |

例如：

```bash
artifacts/builds/mlir-dialect-conversion/conversion-probe partial \
  aicompiler-labs/llvm-mlir/07-dialect-conversion/mixed.mlir
artifacts/builds/mlir-dialect-conversion/conversion-probe full \
  aicompiler-labs/llvm-mlir/07-dialect-conversion/mixed.mlir
```

成功返回 0 并打印转换后 IR；转换失败返回 1，输入解析/验证错误返回 2。故意失败的命令应检查具体诊断，不能把任何非零值都算作符合预期。它是独立驱动程序，因此显式加载规则会创建的 Arith dialect；Pass 工具则通过 `getDependentDialects` 完成对应工作。

要一起观察上述过程并保存命令、输入对应的输出和诊断，可以运行：

```bash
python3 aicompiler-labs/llvm-mlir/07-dialect-conversion/observe.py
```

脚本会逐项展示输入、执行的具体命令、IR 和失败原因。日志在 `artifacts/logs/mlir-dialect-conversion/`，完整生成代码在 build 的 `reference/` 中。

## 一项有限的动手任务

先阅读正文并预测：如果编译阶段允许 mixed 中的 addi 留下，怎样让 **full conversion** 成功？

1. 在 `ClampToArith.cpp` 的目标配置中增加允许 addi 的声明，不改 clamp 展开规则。
2. 重新构建，对 mixed 使用 full，确认 clamp 消失、addi 保留。
3. 从输出追踪 addi 的第一个 operand，确认它引用 minsi 的结果；只看命令成功还不够。
4. 再将该声明改成禁止 addi，预测 partial 的结果并核对失败原因。

完成后保留自己的改动或 diff，并解释“未表态、允许、禁止”三种情况下模式的差异。参考工程默认的 full 对 mixed 失败是有意设置的行为；修改目标后，作者回归中的相关预期也需要相应调整，不应为了追求全部 passed 而撤销自己的实验结论。

`chain.mlir` 提供另一项观察：第一条 clamp 的结果被第二条和最后的 maxsi 同时使用；转换后两处引用都应接到第一条展开的 minsi。它不要求新增类型或接口。

## 文件与验证范围

- `ClampToArith.cpp`：目标、唯一展开规则、模块 Pass。
- `Conversion.h`：Pass 与观察工具共享的入口。
- `my-convert-opt.cpp`：注册已有方言和转换 Pass。
- `conversion-probe.cpp`：同一组实现的模式/目标对照。
- 四份 `.mlir`：基本输入、混合操作、依赖链、动态合法性反例。

维护者运行：

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_conversion.py
```

检查正文摘录与编译源码、实际输出、full/partial 与动态规则的成功/失败、两处 use 的替换、重复转换、极值与等边界、parser/verifier 和 conversion 失败阶段。验证的是编译器侧行为；没有执行转换后的机器码，也没有测性能。
