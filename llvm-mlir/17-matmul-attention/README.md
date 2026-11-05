# Matmul 与 Attention 的编译贯通

正文位于 blog `mlir/tutorials/kernels/` 的 Matmul、Attention 与在线 Attention 三篇。这里把分块后的表示、对象编译、数值参考和有限修改集中起来。

## Matmul：先追踪同一个 C 块

`matmul.mlir` 先 fill 零再累加，`tile.mlir` 选择 BM=2、BN=3、BK=4，`unroll.mlir` 再把 K 块循环展开两倍。两份调度没有创建另一套算法。

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/17-matmul-attention/matmul.mlir \
  --transform-preload-library=transform-library-paths=aicompiler-labs/llvm-mlir/17-matmul-attention/tile.mlir \
  --transform-interpreter --canonicalize
```

先预测 5×7×11 的最后一个输出/归约块，再检查三项 affine.min、三个 subview、外层唯一的 fill。subview 共享原存储，不等于数据已自动进入寄存器或 shared memory。

```bash
python3 aicompiler-labs/llvm-mlir/17-matmul-attention/observe.py --stage unroll
```

观察步长 8 的主循环、两个 matmul，以及处理剩余 K 块的路径。K=11 的贡献区间应为 [0,4)、[4,8)、[8,11)，每段恰好一次。

## Attention：先追踪 m、l、u

两种实现的函数签名都是 Q、K、V、输出、有效长度、scale。形状为 Q[M,D]、K[N,D]、V[N,P]、O[M,P]；每行有效 key 为前缀 `[0,lengths[i])`。要求维度相容、输入输出不重叠、长度在 [0,N]、输入及分数有限。空有效集合明确返回全零。

- `attention.mlir` 分配 M×N 分数存储，逐行改写为指数权重后计算结果。
- `online.mlir` 只分配三个 f32 的临时块。m/l 由 iter_args 携带，未归一化 u 暂存在输出行，结束后归一化。

分数 `[0,0,0,ln(2)]`、value `[10,20,30,40]` 的正确结果是 28。第一块状态为 (0,3,60)，第二块更新后为 (ln(2),2.5,70)。若只缩放 l 而遗漏旧 u，结果变成 40。

```bash
python3 aicompiler-labs/llvm-mlir/17-matmul-attention/observe.py --stage native
```

观察脚本显示实际编译命令、IR 和结果：三种 Matmul×8 组形状，以及两种 Attention×12 组输入，共 48 组数值结果。结果与独立 double 参考比较，并检查分配边界。CPU 对象由固定 LLVM 20.1.8 产生，系统 Clang 仅编译/链接 C 调用程序。

描述符使用 64 位 index/pointer、连续 identity layout、offset=0；aligned 指向哨兵之后的首个有效元素。不要用 identity-layout MemRef 声明却随意传入非零 offset/任意 strides；这类实验应同时更改 IR 的布局约定。

## 有限修改任务

1. 将 Matmul tile_sizes 改成 `[3,2,5]`，预测 5×7×11 的余块，比较同一个 C 视图在 K 循环里的更新。
2. 将在线 Attention 块大小从 3 改成 4，同步修改常量、临时类型及所有使用它的 load/store/dealloc 类型。N=7 应有 4+3 两块，数值仍满足参考容差。
3. 在 scratch 副本里删除 u 的 rescale，先手算四 key 例子的错误结果，再运行对照。保留正确参考文件。
4. 解释全 mask 行如何避免 `-inf-(-inf)` 和除零，再设计一组含空行/非空行的 lengths。

不要求在本实验实现 GPU FlashAttention。当前在线实现用于验证状态递推与存储规模，没有硬件布局、异步流水、Tensor Core 指令或性能结论。

作者维护入口：

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_attention.py
```

manifest 保存源文件/正文哈希、真实命令、数值输出与安全错误版本。测试接受有界误差，不宣称不同归约顺序逐 bit 一致。
