# 多组 operands、Properties 与 Type/Attribute 存储

先预测 `9+2×4+3×5` 的结果，再观察一串 operands 怎样由 [2,2,1] 分成 inputs、weights、seed；追加一对 2×4 后，长度和结果怎样改变。另一个例子规划 2×3 f32 数据块：从偏移 5 按 16 对齐，得到范围 [16,40)。

## 构建与直接命令

在 workspace 根：

```bash
cmake -S aicompiler-labs/llvm-mlir/20-ods-storage \
  -B artifacts/builds/mlir-ods-storage -G Ninja \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DCMAKE_C_COMPILER=/usr/bin/clang -DCMAKE_CXX_COMPILER=/usr/bin/clang++ \
  -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/builds/mlir-ods-storage -j 2
artifacts/builds/mlir-ods-storage/my-opt \
  aicompiler-labs/llvm-mlir/20-ods-storage/input.mlir \
  --my-inspect-segments --my-lower-sums --canonicalize
artifacts/builds/mlir-ods-storage/storage-probe
```

加 `--my-append-pair`（在 inspect/lower 之前）观察 [3,3,1] 与 40。`--mlir-print-op-generic` 展示 Properties：operandSegmentSizes/groupSizes 是固有字段，my.note 是此例可丢弃说明。

## 观察结果

- 两组加权计算：32；无项且无 seed：0。
- 子组 [[2,3],[4],[]]：三个结果 5、4、0，最后空组没有消失。
- 修改原 C++ shape 数组后，创建过的 TileType 仍为 [2,3]；重复构造同 key 的句柄相等。
- Type/Attr Interface 提供 24 字节和 16 对齐；capacity64 成功，capacity32 和不支持类型拒绝。
- 手写 NodeType 以名字确定身份，首次定义 body、重复相同 body 成功，冲突定义失败；别名句柄看到同一 body。

TileType 是教学用“正静态形状、连续 f32”契约，不是一般张量内存大小模型。NodeType 只展示 C++ 构造，无 parser/printer/lowering，不能直接放入文本 IR。本例参考固定上游 `mlir/test/lib/Dialect/Test/TestTypes.h` 的递归类型构造原则。

```bash
python3 aicompiler-labs/llvm-mlir/20-ods-storage/observe.py
python3 aicompiler-labs/llvm-mlir/docs/validate_ods_storage.py
```

observe 展示真实接口/存储查询与前后 IR；validate 保存往返、约束诊断、变化前后结果、源码/文档哈希。32/40 来自实际展开及常量折叠，不冒充机器码执行；C++ 规划器和存储检查是真实程序运行，但没有目标 buffer 分配。

## 有限任务

1. 删除 seed，先写出预期分段与结果。
2. 将最后一个空子组删除，解释为什么 result 个数必须同步改变。
3. 将 Tile 改为 [2,4]，预测字节数和终点。若增加行 padding，先修改接口契约，再改计算。

定义在 MyOps.td，展开消费者在 Segments.cpp，参数/接口实现位于 MyOps.cpp，存储检查在 storage-probe.cpp。不要编辑生成的 .inc。
