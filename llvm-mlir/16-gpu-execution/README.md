# GPU 表示、依赖与编译产物

本实验连接长度 10 的逐元素计算、四线程共享存储轮转和 Host/Device 编译。正文分别在 blog 的 `dialects/gpu/` 与 `compiler/targets/`。输入和关键结果已在正文解释；这里用于实际观察与修改。

## 1. 先预测，再看分工

`launch.mlir` 用 grid=(3,1,1)、block=(4,1,1) 计算 `i=4*block_x+thread_x`，只在 i<10 时计算 `y[i]=2*(x[i]+1)`。先写出第三个 block 的四个 i，再看抽离结果：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/16-gpu-execution/launch.mlir \
  --gpu-kernel-outlining
```

输出含 host 的 `gpu.launch_func` 与设备 `gpu.func`；捕获值成为参数，尾部条件仍在。它没有执行 kernel。另一条入口 `parallel.mlir` 先表达抽象循环：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/16-gpu-execution/parallel.mlir \
  --gpu-map-parallel-loops --convert-parallel-loops-to-gpu
```

`forall.mlir` 配合 `map-forall.mlir` 展示 Transform 映射。观察脚本会原样显示命令与结果，便于对照两条入口：

```bash
python3 aicompiler-labs/llvm-mlir/16-gpu-execution/observe.py --stage mapping
python3 aicompiler-labs/llvm-mlir/16-gpu-execution/observe.py --stage lower
```

`lower` 同时显示地址空间、`nvvm.barrier0` 和 host runtime wrapper。注意 host 阶段仍保留 `gpu.launch_func`，启动调用由后续 LLVM translation 消费设备对象后生成。

## 2. 把不同证据分开观察

| 输入/产物 | 要追踪的关系 | 本实验能证明什么 |
|---|---|---|
| launch / parallel / forall | 迭代点→执行实例→尾部条件 | 工具接受并产生预期表示；模型检查有效点覆盖 |
| shared | global→workgroup→邻居读取→global | 空间与 barrier 的降低；轮转结果仅语义推演 |
| async | 注册→分配→H2D→kernel→D2H→释放→wait→取消注册 | 实际 host 调用与设备 IR 的编译 |
| models.json | 有效点、读写先后、bank、slot 复用 | 显式有限模型中的结果；不是硬件内存模型模拟器 |
| PTX / cubin / host.o | 设备入口、同步指令、运行时符号 | 序列化/汇编/对象编译；不覆盖链接、加载与设备执行 |

```bash
python3 aicompiler-labs/llvm-mlir/16-gpu-execution/observe.py --stage models
python3 aicompiler-labs/llvm-mlir/16-gpu-execution/observe.py --stage device
```

模型输出 N=10、block=4 时每个有效点恰好访问一次；八事件的 2520 种线程内有序排列中有 1432 种过早读取。stride=32 与 33 的 bank 映射分别使用 1 与 32 个 bank。双缓冲缺少复用边时读到 `[10,60]`，而非完整的 `[10,20]`。这些都是模型观测，不能写成 GPU 实测。

`device` 需要 LLVM 20.1.8 编入 NVPTX，示例目标为 sm_80/+ptx70；系统 ptxas 路径为 `/usr/local/cuda/bin/ptxas`。脚本输出完整命令，将 PTX 交给 ptxas，并把含设备对象的 host 模块翻译成 LLVM IR、编译成 CPU 目标文件。选择目标不等于探测到了本机 GPU。

## 3. 有限练习

1. 复制 `launch.mlir`，把长度改为 11、block 大小改为 8。先给出 grid、有效线程与空线程，再验证 outlining 后的常量与 guard。不要只改类型而忘记上界。
2. 在四线程轮转中，把邻居关系改成 `(t+2)%4`。写出输入 `[10,20,30,40]` 的预期输出，说明现有 barrier 为什么仍适用。只检查 IR 不能替代设备数值验证。
3. 修改 `map-forall.mlir` 的 block_dims 为 `[2,1,1]`，保留内部四次 forall。观察诊断，说明当前映射为什么无法用这份分工表示所有迭代。
4. 根据双缓冲表画出前三块依赖。删除 `K0→C2` 后给出一次错误读的顺序；不要在真实设备上通过执行数据竞争来充当正确性实验。

练习答案由学习者实现，参考输入保持可复现。

## 4. 作者验证与限制

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_gpu.py
# 只做 IR、模型和 NPU 源码核对，不声称完成设备序列化：
python3 aicompiler-labs/llvm-mlir/docs/validate_gpu.py --without-serialization
```

manifest 明确记录 serialization 与 device_execution，两者不能混用。当前 WSL 环境访问 GPU 被系统阻止；本实验没有设备执行或性能结果，也不把 `nvidia-smi` 失败当作编译失败。

NPU 篇读取 `upstream/AscendNPU-IR` 的固定提交 `37c6ebc33d1789500014e6a7b2b62164b3cb566b`，验证定义/pipe/内存规划/集成输入的源码位置，保存文件哈希。未构建其 LLVM fork 和 CANN 工具链；标准 MLIR 20.1.8 不负责验证 HIVM 自定义语法。
