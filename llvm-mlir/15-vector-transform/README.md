# Vector 与 Transform 调度

本实验把 `y[i]=2*(x[i]+1)` 的标量、自动向量化、transfer、显式 mask 和完整块/余块五种实现放在一起，观察实际向量 IR、尾部行为和目标代码。另有 2×4 值转置、归约与 2×3×2 contraction。原理在 blog 独立讲解；这里提供工具输入、结果和有限改动任务。

## 工具与直接命令

工作区根目录执行，LLVM/MLIR 固定为 20.1.8、commit `87f0227cb60147a26a1eeb4fb06e3b505e9c7261`。需已有 mlir-opt、mlir-translate、llc 和系统 Clang；不额外构建编译器，不要求 GPU。

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/15-vector-transform/elementwise.mlir \
  --transform-preload-library=transform-library-paths=aicompiler-labs/llvm-mlir/15-vector-transform/vectorize.mlir \
  --transform-interpreter --cse --canonicalize --verify-each
```

应看到步长 4 的循环、两个 subview、create_mask、受屏蔽读写和 vector addf/mulf。generic 已消失，未使用的旧输出读取被清理。n=10 时最后视图长度为 2，向量宽度仍为 4。

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/15-vector-transform/elementwise.mlir \
  --transform-preload-library=transform-library-paths=aicompiler-labs/llvm-mlir/15-vector-transform/suppress.mlir \
  --transform-interpreter
```

后一个调度先成功分块，再错误地要求向量化 scf.for。sequence 抑制可抑制失败后仍执行 print；分块与 generic 均保留，不发生回滚。改成 `failures(propagate)` 会失败退出。不要继续使用已消费或因消费父对象而失效的 handle。

## 分阶段观察与执行

```bash
python3 aicompiler-labs/llvm-mlir/15-vector-transform/observe.py --stage automatic --llvm
python3 aicompiler-labs/llvm-mlir/15-vector-transform/observe.py --stage values --llvm
python3 aicompiler-labs/llvm-mlir/15-vector-transform/observe.py --stage reduction --native
python3 aicompiler-labs/llvm-mlir/15-vector-transform/observe.py --benchmark
```

脚本打印输入、直接命令、输出和日志路径。`--native` 生成并执行七个目标文件，不计时；`--benchmark` 另执行微基准。case 行为名称、核对元素数、错误数，sample 行给具体值。

输入输出连续、等长、不重叠。五种逐元素实现检查 11 个长度，另检查转置、两个归约和 contraction，共 59 组判据。正文尾块用 x=[0,...,9] 推演；驱动输入 x[k]=k-2，因此 n=10 末两项实际打印 14、16，保护区仍为 -777。转置四角为 1、11、4、14；求和 10；次序敏感归约 3；收缩输出 59、65、140、155。

Lowering 先处理 mask/transfer，再进入 LLVM；contract/transpose/shape_cast 先用 lower-vectors.mlir 中的 Patterns 拆解。实际命令保存在日志，不承诺任意 Vector 程序都能用相同列表完成降低。

## 计时范围与记录

benchmark.c 对 scalar/automatic/split 使用相同预分配缓冲区。先核对结果、预热 8 次，绑定一个允许的 CPU，再测 9 轮并轮换方案次序。raw 与 bench 单位为 ns/调用，后者是 min/median/max。包含 C ABI 调用和计算，不含分配、初始化和验证。未运行 LLVM opt 中端；llc 使用 `-O3 -mcpu=x86-64`。无多线程、无 AVX2/AVX-512 特化。

正文一次测量的样本、汇编、源文件哈希和配置冻结在 [benchmark-record.json](./benchmark-record.json)。来自 2026-10-04 Microsoft 虚拟化环境，报告 CPU 为 Ryzen 9 7945HX；未锁定物理主机频率/负载。复测生成新日志，不覆盖历史数据，不以必须达到某个加速比判断测试通过。

## 留给学习者的两个任务

1. 复制 vectorize.mlir，将 tile size 与 vector size 一同改成 8。先预测 n=10 的 mask，再观察 IR。核对结果与保护区后比较汇编是否拆成多个向量，不只凭宽度预测速度。
2. 复制 masked.mlir，把有效数改成常量 1。在这个少访问的安全反例上执行，解释 n=1 正常、n=4 漏写。修复后增加 n=6 的观察。不要把 mask 全置 true 后运行越界访问。

源码只沿一条有限链：LinalgTransformOps.td 的 vectorize 契约 → Vectorization.cpp 生成 → VectorToLLVM 降低 → 当前汇编，不必遍历整个子系统。

## 维护回归

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_vector.py
```

验证往返、文内输入、Transform 成功/失败和失效、59 组数值、安全错误 mask 反例、浮点 lowering flags、目标代码形态、当前计时和历史计时表。日志/manifest 位于 artifacts/logs/mlir-docs/*-vector/；作者通过不代表学习者已经完成任务。
