# MemRef、Bufferization 与生命周期观察

这个实验对应 blog 的 `dialects/memref/` 三篇与 `compiler/memory/` 三篇。先预测索引对应哪个元素、哪次更新需要复制，再观察工具的决定与实际结果。原理与关键 IR 已放在正文，实验用于直接运行和有限修改。

所有命令从 workspace 根目录运行，固定 LLVM `llvmorg-20.1.8`，commit `87f0227cb60147a26a1eeb4fb06e3b505e9c7261`。只需已有的 `mlir-opt`；数值观察另需同版本 `mlir-translate`、`llc`、`mlir_c_runner_utils`，以及系统 clang 作为链接器。缺少目标时可构建：

```bash
cmake --build artifacts/builds/mlir-20.1.8 \
  --target mlir-opt mlir-translate llc mlir_c_runner_utils --parallel 2
```

## 1. 按坐标解释视图

| 输入 | 观察内容 | 已初始化输入下的预期 |
|---|---|---|
| `storage.mlir` | alloc → store → load → dealloc | 返回 7 |
| `dynamic.mlir` | 动态行数、dim | 传入 5，返回 5 |
| `view.mlir` | 4×4 中的 2×2 窗口、写入别名、元数据 | 返回 99、5、4、1 |
| `nested-view.mlir` | 嵌套切片与跨步切片 | 原数组为 0…15 时返回 9、10 |
| `cast.mlir` | 擦除布局的静态信息 | 原数组为 0…15 时仍返回 6 |

先直接解析并打印：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/10-memory-bufferization/view.mlir
```

打印合法 IR 不会执行函数。完整数值入口见第 4 节，它会构造已初始化的输入并打印实际值。

## 2. 从旧值使用观察复用决定

输入向量设为 `[10,20,30,40]`，先比较这几份文件：

| 输入 | 改变的条件 | Buffer IR 的预期 |
|---|---|---|
| `reuse.mlir` | 可写，不再读取旧张量 | 直接 store 输入，没有额外 alloc/copy |
| `preserve.mlir` | 同时读取旧值和新值 | alloc + copy + store，返回 10、99、20 |
| `readonly.mlir` | 去掉 writable | 复制后更新，输入第一项仍为 10 |
| `fill-preserve.mlir` | 完整覆盖新结果，仍保留旧值 | 有 alloc，没有初始内容的 copy |
| `tile-update.mlir` | 取窗口、填充、插回 | 复用 subview；清理后无需复制整个数组 |

直接看分析标记：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/10-memory-bufferization/preserve.mlir \
  '--one-shot-bufferize=test-analysis-only print-conflicts'
```

寻找 insert 的 `["none", "false", "none"]`，并把 `CONFL-WRITE` 与 `READ` 对应回输入。将文件换成 `reuse.mlir`，中间条目应为 `true`。

随后真正改写：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/10-memory-bufferization/preserve.mlir \
  --one-shot-bufferize --verify-each

artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/10-memory-bufferization/tile-update.mlir \
  --one-shot-bufferize --cse --canonicalize --verify-each
```

Tile 例子要区分原始 bufferization 与后续清理：同一窗口的两个 subview 先由 CSE 合并，然后 canonicalize 消除自复制。不要仅根据最终 IR 把清理效果全部归因于 One-Shot。

## 3. 沿返回值追踪释放责任

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/10-memory-bufferization/preserve.mlir \
  --one-shot-bufferize --buffer-deallocation-pipeline --verify-each

artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/10-memory-bufferization/call.mlir \
  --buffer-deallocation-pipeline --verify-each

artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/10-memory-bufferization/branch.mlir \
  --ownership-based-buffer-deallocation --verify-each
```

`call.mlir` 的 make 返回新 buffer，因此不在 make 中释放；consume 最后只返回标量，责任在 consume 结束。`branch.mlir` 的中间输出把 memref 与 i1 责任信息一同传出区域。把最后一个命令的 pass 换成 `--buffer-deallocation-pipeline`，可看到简化为按原条件执行 dealloc 的结果。

`return-alias.mlir` 展示默认函数协议怎样处理别名返回。它先引入 `bufferization.clone`，在本实验的后续 lowering 中落实为 alloc/copy；不要通过修改 clone 的源或结果来测试通用 clone 语义，这违反该中间操作的契约。数值驱动只读取内容，并观察具体 lowering 后的分配地址关系。

`signature.mlir` 展示 tensor 参数与返回值转换：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/10-memory-bufferization/signature.mlir \
  '--one-shot-bufferize=bufferize-function-boundaries function-boundary-type-conversion=identity-layout-map'
```

手写 dealloc 的 `storage/dynamic` 与自动释放输入分开处理，不向已经手工管理的输入再次运行自动释放流程。

## 4. 观察入口与本机结果

下面的入口打印输入、实际命令、分析 IR、buffer IR 和加入释放后的 IR；不是只有 passed 摘要：

```bash
python3 aicompiler-labs/llvm-mlir/10-memory-bufferization/observe.py
python3 aicompiler-labs/llvm-mlir/10-memory-bufferization/observe.py \
  --example branch --stage dealloc
python3 aicompiler-labs/llvm-mlir/10-memory-bufferization/observe.py \
  --example preserve --stage buffer --numeric
```

`--numeric` 分别运行手动生命周期与自动生命周期两组程序，打印 28 个有名称的 `actual/expected` 观察，包括窗口偏移、别名写入、非连续复制、旧值保护、完整填充、两条分支以及返回 buffer。命令、输入、LLVM IR、目标文件与可执行文件都保存在打印出的 artifacts 日志目录。

实际编译过程由 `experiment.py` 明确排列：

```text
自动组：One-Shot → buffer-deallocation-pipeline
共同后续：convert-bufferization-to-memref → convert-linalg-to-loops
       → expand-strided-metadata → lower-affine → convert-scf-to-cf
       → convert-to-llvm → reconcile-unrealized-casts
       → mlir-translate → LLVM 20 llc → 系统 clang 链接 → 执行
```

系统 clang 只链接目标文件，避免让旧版 clang 直接解析新版 LLVM IR。具体命令也记录在每次实验的 `*.command.txt` 中，可独立复现。

这些数值检查支持本组具体例子的结论；不测性能，也不构成任意程序的内存安全证明。

## 5. 留给学习者的两个修改任务

请先把参考输入复制到自己的 work 目录，保留原文件便于比较。

**任务 A：改变窗口。** 将 `view.mlir` 的起点从 `[1,1]` 改为 `[0,2]`，大小仍为 `[2,2]`。同步修改结果布局类型、从原数组读取的坐标以及函数中所有相关类型。先算出 offset、strides 和写入对应的原坐标，再运行工具验证。提交修改后的完整 IR，以及一张“窗口坐标 → 原坐标 → 元素偏移”表。

**任务 B：改变旧值读取的时间。** 将 `preserve.mlir` 的 `%old = tensor.extract %t[%c0]` 移到 insert 之前，保持返回的三个数值语义不变。先预测是否仍有冲突，再观察 analysis-only 和真实 buffer 输出。解释为什么标量 `%old` 已经获得后，不再要求数组第一项保持 10。最后去掉 writable，再比较一次：两个条件影响的是同一个决定的不同前提。

不要求从零实现 bufferization，也不要求现在通读分析器源码。完成后可以提交 IR 与观察解释，再安排自定义操作接口或 CPU lowering 的独立任务。

## 作者验证

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_memory.py
```

检查正文与 14 份完整输入对应、打印往返、展示的 9 份输出、分析理由、错误 layout、缺 restrict、未知 tensor 操作边界、所有权结构和 28 个本机标量观察。验证记录进入 `artifacts/logs/mlir-docs/*-memory/manifest.json`，不把作者验证记为学习者已完成任务。
