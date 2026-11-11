# 1:N 转换与声明式规则

两项独立实验共用一个教学 My dialect 工具。先选 pairs 观察类型与值边界，再选 patterns 对照规则表达。

## 构建

workspace 根使用固定 LLVM 20.1.8：

```bash
cmake -S aicompiler-labs/llvm-mlir/21-conversion-patterns \
  -B artifacts/builds/mlir-conversion-patterns -G Ninja \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DCMAKE_C_COMPILER=/usr/bin/clang -DCMAKE_CXX_COMPILER=/usr/bin/clang++ \
  -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/builds/mlir-conversion-patterns -j 2
```

## 1:N 的可见变化

```bash
artifacts/builds/mlir-conversion-patterns/my-opt \
  aicompiler-labs/llvm-mlir/21-conversion-patterns/pairs.mlir --my-flatten-pairs
```

一个 pair Value 变成两个 i32；函数参数/返回、call、cf.br 与目标 Block 都同步变化。缺少 call 规则的 `--my-flatten-no-call` 会按预期失败。

```bash
python3 aicompiler-labs/llvm-mlir/21-conversion-patterns/observe.py --stage pairs
```

显示中间 IR、CPU lowering 和四组 C 输入；每组同时检查加法与减法，避免交换性掩盖顺序错误。这个转换只支持 tuple<i32,i32> 与示例中的边界，不是任意 tuple、条件分支、SCF 或外部 ABI 的通用转换。

## DRR 与 PDLL

DRR 已由 CMake 用 `-gen-rewriters` 生成 MyPatterns.inc 并编译进工具：

```bash
artifacts/builds/mlir-conversion-patterns/my-opt \
  aicompiler-labs/llvm-mlir/21-conversion-patterns/rewrites.mlir --my-apply-drr
```

PDLL 路径先得到可读的规则 IR：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-pdll \
  aicompiler-labs/llvm-mlir/21-conversion-patterns/patterns.pdll \
  -I aicompiler-labs/llvm-mlir/21-conversion-patterns \
  -I upstream/llvm-project/mlir/include -x=mlir \
  -o artifacts/builds/mlir-conversion-patterns/patterns.mlir
artifacts/builds/mlir-conversion-patterns/my-opt \
  aicompiler-labs/llvm-mlir/21-conversion-patterns/rewrites.mlir \
  --my-pdl-file=artifacts/builds/mlir-conversion-patterns/patterns.mlir --my-apply-pdl
```

两个 Pass 都删除右零链，保留左零与非零输入。工具显式注册 IsZero 原生约束。只运行 canonicalize 时四条 my.add 都保留；本操作刻意没有 fold。

```bash
python3 aicompiler-labs/llvm-mlir/21-conversion-patterns/observe.py --stage patterns
python3 aicompiler-labs/llvm-mlir/docs/validate_conversion_patterns.py
```

维护脚本再查往返、错误 pair 数量、不支持 tuple、错误数值域和 PDLL 语法错误，保存产物与哈希。PDL/PDLL 的比较是实际改写输出，不是目标程序数值证明。

## 你的有限任务

1. 给 pair 流程增加一个携带 pair 的控制边界，先画好原参数与目标列表，再补规则。
2. 为 my.add 增加左零规则，选 DRR 或 PDLL 之一即可，保持非零输入不变。
3. 给新规则补会失败的匹配输入，并解释正确性前提；不要直接推广到浮点。
