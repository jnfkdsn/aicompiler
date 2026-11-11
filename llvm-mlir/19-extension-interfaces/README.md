# 自定义操作与通用接口消费者

本实验观察三条完整过程：my.add_one 的读写/别名事实进入 One-Shot；结果 Type 与运行时尺寸进入不同消费者；my.scope 的入口/出口协议让 SCCP 传播常量。教学方言仍叫 my，与之前版本分别构建，不同时链接。

## 先预测，再观察

- 输入 [10,20,30,40]，只读取新值时，原存储能否更新？额外读取旧值后，是否需要分配和复制？
- 只查询 add_one 的动态长度时，能否跳过计算所有元素？问号能否直接成为运行时 SSA 值？
- scope 的输入为 5、内部加 2，通用 SCCP 依靠什么知道结果为 7？

Blog 的自定义 Bufferization、类型/形状推导与区域接口章节已内嵌关键代码和结果；下面提供直接可用的工程命令。

## 构建

在 workspace 根运行，使用固定 LLVM 20.1.8：

```bash
cmake -S aicompiler-labs/llvm-mlir/19-extension-interfaces \
  -B artifacts/builds/mlir-extension-interfaces -G Ninja \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DCMAKE_C_COMPILER=/usr/bin/clang \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++ -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/builds/mlir-extension-interfaces -j 2
```

`my-opt-no-buffer` 读取同样的方言，但不接入 AddOne Bufferizable 外部模型；不是未注册操作的对照。

## 直接观察三个消费者

```bash
artifacts/builds/mlir-extension-interfaces/my-opt \
  aicompiler-labs/llvm-mlir/19-extension-interfaces/bufferization.mlir \
  --one-shot-bufferize --canonicalize

artifacts/builds/mlir-extension-interfaces/my-opt \
  aicompiler-labs/llvm-mlir/19-extension-interfaces/shape.mlir \
  --my-probe-interfaces --resolve-ranked-shaped-type-result-dims --canonicalize

artifacts/builds/mlir-extension-interfaces/my-opt \
  aicompiler-labs/llvm-mlir/19-extension-interfaces/scope.mlir \
  --my-probe-interfaces --sccp --canonicalize
```

依次看到：reuse 无分配、preserve 有新分配但无 copy；动态尺寸改查 input，静态尺寸成为 4，加一消失；scope 的 5→7 传递成为直接返回常量。

control.mlir 还可以用 `--my-probe-interfaces --inline --sccp --canonicalize` 观察函数、调用、if、for。探针输出是通用接口的真实回答；分支与循环的方括号表示沿边关联的值数，不是次数。

## 带 CPU 数值的观察与维护

```bash
python3 aicompiler-labs/llvm-mlir/19-extension-interfaces/observe.py --stage all
python3 aicompiler-labs/llvm-mlir/docs/validate_interfaces.py
```

observe 显示执行命令、中间 IR、查询和 C 数值，并保存所有产物。buffer 阶段执行 ownership pipeline、LLVM lowering、C wrapper 四组数组检查；scope 只验证编译器优化，没有自定义原生 lowering。validate 另查 generic 往返、缺模型、静态错误与未知输入等反例，并记录源码/文档哈希。

AddOne 的调用前提：一维 f32、input/init 运行时同形状。Tensor 类型相同不证明两个动态长度相等；本工程没有通用符号形状证明或运行时 shape assert。Elementwise 声明只因同坐标先读后写而成立。外部模型扩展加载生成循环需要的 Arith/MemRef/SCF；Func inliner 扩展也显式注册。

## 留给你的修改

1. 把加一改为乘二，先列出哪些 Bufferizable 回答不变，再修改计算与 C 期望。
2. 在 shape 函数额外读取结果元素，预测为什么尺寸查询仍可替换，但计算不能删除。
3. 将 scope 的常量输入改成函数参数，解释 SCCP 的结果。若打算增加零次执行分支，先画控制边与初始值映射，不能只改运行代码而沿用当前接口。

不要编辑生成的 .inc。声明改 MyOps.td，协议实现改 MyOps.cpp/Bufferization.cpp，观察消费者在 Probe.cpp。
