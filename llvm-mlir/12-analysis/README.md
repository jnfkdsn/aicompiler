# 分析事实与优化合法性

这个实验回答三类问题：分析读出了什么事实；IR 修改后事实是否仍然有效；依赖这些事实的优化是否保留行为。对应 blog 的 `compiler/analysis/` 五篇。正文已经包含关键输入与结果，实验用于观察、改动和验证，不是另一套阅读前置。

## 构建与直接观察

以下命令在工作区根目录执行，依赖已有 LLVM/MLIR 20.1.8 构建。产物保存在 artifacts，不写进工程目录。

```bash
cmake -G Ninja -S aicompiler-labs/llvm-mlir/12-analysis \
  -B artifacts/builds/mlir-analysis-docs \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DLLVM_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/llvm" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/builds/mlir-analysis-docs -j 2
artifacts/builds/mlir-analysis-docs/inspect-analysis dominance \
  aicompiler-labs/llvm-mlir/12-analysis/dominance.mlir
```

先预测五行输出：外层 base 能否供分支内使用，局部 local 能否供函数 return 使用，if result 能否供 return 使用，以及 if 后两个值是否活跃。实际结果依次为 `1,0,1,1,0`。

查询工具的各模式是针对下表固定教学结构的观察程序，并非任意 IR 的通用检查器。编辑输入时保留所查询函数和操作结构；完整通用工具应补结构查找与错误处理。

| 模式 | 输入 | 可观察变化 |
|---|---|---|
| dominance | dominance.mlir | 层次支配与 if 之后的活跃性 |
| cfg | cfg.mlir | 菱形 CFG 的支配和后支配 |
| alias | alias.mlir | 参数可能别名、独立分配、view 来源和 store 的 ModRef |
| constants | constants.mlir | sum=7、if result=7、out unknown |
| ranges | ranges.mlir | 循环 i=0..3、next=1..4 |
| cache / stale | dominance.mlir | 正常失效重算；错误 preserve 导致缓存为 9 而当前为 10 |
| calls | calls.mlir | entry→helper 与外部 callee 边界 |

例如查看缓存反例与实际优化：

```bash
artifacts/builds/mlir-analysis-docs/inspect-analysis stale \
  aicompiler-labs/llvm-mlir/12-analysis/dominance.mlir
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/12-analysis/optimizations.mlir \
  --cse --loop-invariant-code-motion --verify-each
```

`stale` 故意使用错误保留声明；它输出 `stale=1`，但工具成功退出，因为这是观察缓存问题而不是生成非法 IR。不要把该保留声明复制到真实修改 Pass。

## 按主题观察

```bash
python3 aicompiler-labs/llvm-mlir/12-analysis/observe.py --topic dominance
python3 aicompiler-labs/llvm-mlir/12-analysis/observe.py --topic alias
python3 aicompiler-labs/llvm-mlir/12-analysis/observe.py --topic cache
python3 aicompiler-labs/llvm-mlir/12-analysis/observe.py --topic constants
python3 aicompiler-labs/llvm-mlir/12-analysis/observe.py --topic legality --native
```

脚本先打印输入和所观察的问题，再打印实际命令与分析/变换结果。`--native` 将优化前后的同一输入分别转换为 LLVM IR，经固定版本 llc 生成目标文件，以系统 clang 仅作 C 编译及链接，再运行 `driver.c`。每个版本核对 15 个标量观察，包括参数别名、写入后内容、零次循环与除数为零但不执行除法的合法路径。

两套结果一致不等于穷举证明，也没有测量性能。此例的通用 CSE 使用有限的读效果检查，不应从未合并推出任意专门分析都无法优化。

## 两个有限练习

1. 复制 `constants.mlir` 到自己的工作文件，把 else 中的 7 改成 8。先预测三个事实，再运行 constants 查询。随后在函数内部增加 true 常量并让 if 使用它，解释为什么结果再次改变。提交两份 IR 和三行预测，不需要改 C++ 框架。
2. 复制 `optimizations.mlir`，把除法函数中的未知除数改成常量 2，保持结果被使用。先解释原先阻止外提的条件发生了什么变化，再查看固定版本 LICM 的实际行为。若结果与预测不同，沿 `DivSIOp::getSpeculatability` 和 LICM 条件定位；不能仅以“没移动”判断数学上不合法。

作者的维护验证：

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_analysis.py
```

它核对正文标记输入/输出、7 份完整 IR 的往返、真实分析查询、分支合流/可达性变体、非法支配诊断、缓存失效正反例、CSE/LICM 结构和 30 个本机标量观察。命令、输出、正文及源码哈希写入 `artifacts/logs/mlir-docs/*-analysis/manifest.json`。通过计数不作为个人完成练习的记录。
