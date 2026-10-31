# Tensor / Linalg：从坐标关系到实际结果

这组实验配合 blog 的编译流程导读、Tensor 三篇和 Linalg 三篇。正文中的输入、推演和关键结果可以独立阅读；这里用于预测、运行、修改与比较。

## 先观察一个例子

从 workspace 根目录执行：

```bash
python3 aicompiler-labs/llvm-mlir/09-tensor-linalg/observe.py
```

默认显示矩阵加法的输入、buffer 形式和循环形式，同时打印实际命令。先定位 `(i,j)=(1,2)`：输入 A 的 6 和 B 的 60 怎样在循环中读取，得到的 66 写到哪里。

也可以指定同目录的其他输入：

```bash
python3 aicompiler-labs/llvm-mlir/09-tensor-linalg/observe.py --example patch
python3 aicompiler-labs/llvm-mlir/09-tensor-linalg/observe.py --example row-sum
python3 aicompiler-labs/llvm-mlir/09-tensor-linalg/observe.py --example destination-old-use
```

patch 观察窗口如何落实为存储访问；row-sum 观察初始化与累积；old-use 观察怎样同时保持旧值和新结果。具体分配与复制属于当前 pipeline 的选择，不能把某个打印结果当成所有 pipeline 的唯一形式。

## 示例与阅读位置

| 输入 | 要追踪的关系 | 正文 |
|---|---|---|
| `add.mlir` | 完整矩阵加法及三个阶段 | [编译流程导读](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/tutorials/pipelines/overview.md)、[迭代空间](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/dialects/linalg/iteration_maps.md) |
| `element-update.mlir`、`dynamic-shape.mlir`、`generate.mlir`、`shape-cast.mlir` | 新旧值、运行时尺寸、坐标构造与形状信息 | [Tensor 值与形状](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/dialects/tensor/values_shapes.md) |
| `patch.mlir`、`strided-slice.mlir`、`dynamic-slice.mlir`、`rank-reduce.mlir` | 窗口局部索引与源坐标、插回与降秩 | [切片与更新](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/dialects/tensor/slices.md) |
| `reshape.mlir`、`dynamic-reshape.mlir`、`reshape-shape-operand.mlir` | 元素顺序、相邻维度分组与动态 shape | [形状变换](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/dialects/tensor/reshape.md) |
| `add-dynamic.mlir` | 两个动态维度必须满足同一尺寸条件 | [迭代空间](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/dialects/linalg/iteration_maps.md) |
| `broadcast.mlir`、`row-sum.mlir`、`matmul.mlir` | 投影、累积位置、named/generic | [广播、归约与矩阵乘法](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/dialects/linalg/structured_computations.md) |
| `destination-old-use.mlir` | outs 对应结果，同时保留旧张量 | [DPS](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/dialects/linalg/destination_style.md) |

这些链接使用 blog 仓库地址；新文件推送后才可在线访问。本实验不定义另一套自定义 dialect。

## 直接执行阶段转换

已有的固定 LLVM 20.1.8 构建提供 `mlir-opt`。查看 buffer 形式：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/09-tensor-linalg/add.mlir \
  --empty-tensor-to-alloc-tensor \
  --one-shot-bufferize='bufferize-function-boundaries function-boundary-type-conversion=identity-layout-map' \
  --verify-each
```

继续展开循环：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/09-tensor-linalg/add.mlir \
  --empty-tensor-to-alloc-tensor \
  --one-shot-bufferize='bufferize-function-boundaries function-boundary-type-conversion=identity-layout-map' \
  --convert-linalg-to-loops --lower-affine --verify-each
```

前一个阶段保持结构化计算，只安排存储；后一个阶段将 maps 与 body 落实为循环、load 和 store。完整 `LLVM_FLAGS` 保存在 `experiment.py`：切片等输入还要展开 stride/offset 信息，再降低 affine、SCF 和其他操作并清理 cast。

观察 named matmul 对应的通用结构：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/09-tensor-linalg/matmul.mlir \
  --linalg-generalize-named-ops
```

## 执行与数值对照

作者验证使用同一 LLVM 版本的 `llc` 生成本机目标文件，系统 Clang 只负责链接。这样不要求旧版 Clang 解析新版 LLVM IR。首次需要补建两个已有配置的目标：

```bash
cmake --build artifacts/builds/mlir-20.1.8 \
  --target llc mlir_c_runner_utils -j2
python3 aicompiler-labs/llvm-mlir/09-tensor-linalg/observe.py --numeric
```

数值观察按源函数分组，打印实际标量和预期值。109 个观察覆盖完整小张量、旧/新值、动态窗口、reshape、广播、行和、matmul，以及非零初始值、零长度归约和零行输入。使用的 f32 测试数据是可精确表示的小整数，不据此宣称一般浮点误差已经验证。

`numeric_cases.py` 生成普通 MLIR 驱动，逐个读取结果元素进行比较，并调用运行时打印。实际执行链为：

```text
numeric-input.mlir → mlir-opt → LLVM dialect
    → mlir-translate → numeric.ll
    → 同版本 llc → numeric.o
    → 系统 clang 链接 MLIR 运行时 → 本机程序
```

`experiment.py` 保存每条真实命令和输出，包括 `numeric-observations.json`，不依赖只返回一个 passed 计数。程序是短生命周期的功能检查；当前未加入完整 buffer 释放策略，不是长期运行的内存管理或性能示范。

## 两个可独立完成的任务

1. 复制 `broadcast.mlir`，改成按行加 bias：把 bias 长度改为 2，并修改其 map。使用 `[10,20]`，先写出完整预期矩阵，再观察循环访问。不要只把数据换成全 1。
2. 复制 `row-sum.mlir`，改成列和。调整结果形状、输出 map 与 iterator；对于 A=`[[1,2,3],[4,5,6]]`，结果应为 `[5,7,9]`。解释为什么只交换 iterator 文本还不够。

可以先把个人版本放在独立练习目录，保留这里的参考输入。数值驱动目前为固定例子设计；改动算法后也需要按新接口增加相应调用和预期，不要为了消除失败而机械改答案。

## 文档维护检查

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_tensor_linalg.py
```

验证正文与输入一致、generic 往返、阶段完整输出、named generalization、静态 dim 折叠、五类静态不合法输入，以及本机数值结果。日志与带文件哈希的 manifest 写入 `artifacts/logs/mlir-docs/`。不重跑无关的 Conversion 或自定义方言工程；不把作者参考实现记为学习者已完成任务。
