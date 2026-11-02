# Math/Index 与 Softmax 数值基线

四篇正文分别解释标量数学的实现、尺寸/边界计算、完整 Softmax 表示与按行存储调度。这里提供可观察工程，关键过程和代码已在 blog 内嵌。

## 输入与接口

| 文件 | 职责 | 约定 |
|---|---|---|
| math.mlir | exp、exp-1、expm1 | f32；比较 libm 与固定版本 LLVM 展开 |
| index.mlir | ceildivu 块数、位宽相关常量除法 | 除数非零；32 位只核对转换，64 位本机运行 |
| softmax.mlir | M×N Tensor、Max→Exp→Sum→Normalize | 有限 f32 输入；N>0 为普通概率行 |
| row-softmax.mlir | 按行求 max，exp/sum 融合，输出作暂存 | 连续 MemRef，输入输出同形状且不重叠；无内部分配 |

M=0 返回空批。N=0 是本实验明确选择的空输出扩展，不要求行和为 1；NaN、正无穷和全负无穷 mask 行不在当前算法契约内。

## 直接观察命令

在 workspace 根目录执行。已有工具链为 LLVM/MLIR 20.1.8。

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/13-softmax/math.mlir --convert-math-to-libm
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/13-softmax/index.mlir --canonicalize
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/13-softmax/softmax.mlir \
  --one-shot-bufferize='bufferize-function-boundaries function-boundary-type-conversion=identity-layout-map' \
  --cse --canonicalize
```

先预测三个结果：Math 出现哪些外部调用；位宽相关的 index.divu 是否被折叠；Softmax 出现几个分配。实际分别为 expf/expm1f、保留除法、四个分配。继续加入 `--buffer-deallocation-pipeline` 可观察内部三个分配的释放，返回结果由调用方释放。

## 观察入口与本机对照

```bash
python3 aicompiler-labs/llvm-mlir/13-softmax/observe.py --example softmax --stage buffer
python3 aicompiler-labs/llvm-mlir/13-softmax/observe.py --example row-softmax --stage llvm
python3 aicompiler-labs/llvm-mlir/13-softmax/observe.py --native
```

脚本打印实际输入、阶段 IR 与执行命令。`--native` 展示每组输入的最大绝对/相对误差、行和误差，以及三元素行的具体输出；不是只输出 passed。

编译链是 One-Shot → 释放 → Linalg/SCF lowering → MathToLibm/IndexToLLVM → LLVM dialect → mlir-translate → 固定版本 llc → 系统 clang 编译 C 并链接。数学库用 `-lm`，运行时辅助函数使用同版本 `mlir_c_runner_utils`。系统 clang 不读取 LLVM20 IR。

`driver.c` 对 10 组输入和形状测试两份 Softmax，参考对实际 f32 输入用 double 计算。判据为 `abs_error <= 2e-6 + 2e-5*abs(reference)`，非空行的行和误差不超过 `5e-5`，并检查有限/非负、形状、输入未修改及输出外哨兵。max-relative 的报告分母下限为 1e-30，不单独作为通过判据。

标量观察包括 exp/极小 expm1、零与非整除尺寸、64 位无符号边界。宽整数采用精确整数比较，避免 double 掩盖低位错误。MathToLLVM 的 expm1 展开在 1e-8 处得到 0，libm 路径保留非零结果，这是所用版本/宿主的行为观察。

## 两个有限练习

1. 复制 softmax.mlir，把最大值初值从负无穷改成 0。分别预测全正小输入和全负大输入会出现什么；解释为什么 `[1,2,3]` 单一用例不足以暴露这个错误。作者验证有独立副本，不修改你的工作文件。
2. 从按行版本出发，画出一种“第二遍只求和，第三遍重算 exp 再归一化”的调度，统计 exp 次数与存储需求。先完成推演，再按兴趣改 IR；不要在未测量时声称它更快。

## 维护检查

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_softmax.py
```

检查完整正文输入和往返、两种 Math 路径、32/64 位 index 转换、四个分配/三个释放、两实现数值与错误归约初值的负例。日志和哈希位于 `artifacts/logs/mlir-docs/*-softmax/manifest.json`。当前没有计时、GPU/NPU 执行或通用自动 fusion Pass 的效果证明；按行版本是手工推导的等价实现。
