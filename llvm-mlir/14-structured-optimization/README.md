# Affine 与结构化变换

配套 Affine 三篇与 tiling/fusion/interchange 三篇。先观察域、访问和结果，再理解用于复现调度的 Transform 脚本；完整 Transform handle 协议在后续章节展开。

## 案例

| 输入 | 要观察的事实 |
|---|---|
| crop.mlir | 3×4 窗口从 6×8 输入的 (1,2) 起点读取，输出首尾 102、305 |
| triangle.mlir | Integer Set 与两个循环域相交，得到 4×4 下三角 |
| affine-add.mlir | 5×7 独立加一，按 2×3 分块后的最后一块为 1×1 |
| elementwise.mlir | `(x+1)*2` 两阶段合并为一个 generic，再分块或交换迭代维 |
| wave.mlir | 跨行递推依赖 (1,-1)，外层不并行、不能交换两层循环 |
| tile.mlir / interchange.mlir | 可单独预加载的固定版本 Transform 调度 |

存储参数须满足相应形状、有效范围与正文的不重叠条件。本实验不对任意外部输入自动生成边界保护。

## 直接观察变换

在工作区根目录使用已有 LLVM/MLIR 20.1.8 工具链：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/14-structured-optimization/affine-add.mlir \
  --affine-loop-tile='tile-sizes=2,3' --verify-each
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/14-structured-optimization/elementwise.mlir \
  --linalg-fuse-elementwise-ops --canonicalize --verify-each
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/14-structured-optimization/elementwise.mlir \
  --linalg-fuse-elementwise-ops --canonicalize \
  --transform-preload-library=transform-library-paths=aicompiler-labs/llvm-mlir/14-structured-optimization/tile.mlir \
  --transform-interpreter --cse --canonicalize --verify-each
```

第一条观察四层循环与 min 余块；第二条观察 generic 从两个变为一个；第三条观察循环携带 tensor、切片长度、extract/insert。替换 library 文件为 interchange.mlir 可以看到 `(d0,d1)->(d1,d0)`，结果 tensor 的物理布局并没有因此转置。

## 真实依赖查询

```bash
cmake -G Ninja -S aicompiler-labs/llvm-mlir/14-structured-optimization \
  -B artifacts/builds/mlir-structured-docs \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DLLVM_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/llvm" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/builds/mlir-structured-docs -j 2
artifacts/builds/mlir-structured-docs/inspect-dependence \
  aicompiler-labs/llvm-mlir/14-structured-optimization/wave.mlir
```

工具限定一个两层完美 affine loop nest，打印 identity/swap 合法性和内外层并行性。wave 结果为 `1,0,0,1`，独立 affine-add 为 `1,1,1,1`。它查询事实，不实施交换或并行化。

## 按主题与数值观察

```bash
python3 aicompiler-labs/llvm-mlir/14-structured-optimization/observe.py --stage affine-tile
python3 aicompiler-labs/llvm-mlir/14-structured-optimization/observe.py --stage fused
python3 aicompiler-labs/llvm-mlir/14-structured-optimization/observe.py --stage tiled
python3 aicompiler-labs/llvm-mlir/14-structured-optimization/observe.py --stage swapped
python3 aicompiler-labs/llvm-mlir/14-structured-optimization/observe.py --stage dependence --native
```

native 编译原始/融合/分块/交换四套逐元素函数，核对 7 组形状的全部坐标和输入未修改；另外核对 crop、triangle、Affine 分块、递推以及错误交换确实改变结果。输出 sample 显示递推的 `[2,0]` 从 4 变为 102。这个错误对照没有越界或除零，使用的是仍有定义的错误算法，不能把它当成合法优化参考。

## 两个有限练习

1. 将 tile 大小改为 3×4，先列出 5×7 的块起点与每块大小，再执行变换核对 min 和切片。额外考虑 0×7 和 1×1，不需要先改求解器。
2. 在自己的 wave 副本中把读取改为 `a[i-1,j]`。推导新依赖方向，再查询交换与并行性。说明为什么“交换合法”仍不等于“i 可以无协议地并行”。

## 作者检查与范围

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_structured.py
```

验证正文输入、7 个算法/调度文件往返、变换结构和分配变化、真实依赖事实、错误 symbol/非仿射乘法/非排列诊断，以及 33 组本机结果判据。此版本 affine.apply 不完整检查 symbol 合法性，拒绝用例放在实际检查该条件的 affine.if 上。

所有命令和哈希保存于 `artifacts/logs/mlir-docs/*-structured/manifest.json`。代码生成使用固定版本 llc，系统 clang 仅编译/链接 C。当前未做计时；更少分配或不同循环顺序不作为性能结论。
