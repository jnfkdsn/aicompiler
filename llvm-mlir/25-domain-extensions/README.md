# 25：领域表示的有限观察

这组输入服务于Quant/Sparse/Shape/IRDL/Complex/TOSA的范围定位，不是六套完整编译器。

## 直接命令

workspace根目录，固定mlir-opt为artifacts/builds/mlir-20.1.8/bin/mlir-opt：

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt aicompiler-labs/llvm-mlir/25-domain-extensions/quant.mlir
artifacts/builds/mlir-20.1.8/bin/mlir-opt aicompiler-labs/llvm-mlir/25-domain-extensions/sparse.mlir --sparse-reinterpret-map --sparsification
artifacts/builds/mlir-20.1.8/bin/mlir-opt aicompiler-labs/llvm-mlir/25-domain-extensions/shape.mlir --pass-pipeline='builtin.module(func.func(convert-shape-constraints,canonicalize))'
artifacts/builds/mlir-20.1.8/bin/mlir-opt aicompiler-labs/llvm-mlir/25-domain-extensions/dynamic.mlir --irdl-file=aicompiler-labs/llvm-mlir/25-domain-extensions/my.irdl.mlir --canonicalize
artifacts/builds/mlir-20.1.8/bin/mlir-opt aicompiler-labs/llvm-mlir/25-domain-extensions/complex.mlir --convert-complex-to-standard --canonicalize
artifacts/builds/mlir-20.1.8/bin/mlir-opt aicompiler-labs/llvm-mlir/25-domain-extensions/tosa.mlir --pass-pipeline='builtin.module(func.func(tosa-to-linalg))'
```

观察：量化类型保留映射；CSR转为positions/coordinates/values循环；动态shape条件变cf.assert；IRDL只提供结构约束，没有Pure所以死my.add仍在；复数常量展开折叠为-5/10；TOSA加法成为Linalg访问关系与标量区域。

```bash
python3 aicompiler-labs/llvm-mlir/25-domain-extensions/observe.py
python3 aicompiler-labs/llvm-mlir/docs/validate_domains.py
```

完整命令、IR、模型结果和哈希记录在artifacts/logs/mlir-docs/*-domain-extensions。

models.py是独立Python语义模型：7个量化值（最近偶数舍入/饱和）、4个CSR初值/空行组合及复数乘法。没有执行MLIR生成的机器程序。Sparse还需后续存储/运行时lowering；Shape只转换约束；StableHLO只提供官方项目定位，未安装/构建。

## 选一项练习

- Quant：修改zero point，推演零padding的存储值。
- Sparse：增加空行，解释positions边界与outs初值保留。
- Shape：比较[M,1]+[N]与[M,K]+[N]需要的动态约束。
- IRDL：改为i64约束，验证原i32程序为何失败；不要把允许未知操作当作验证。
- Complex：第二个输入改为3-4i，预测实部/虚部。
- TOSA：指出转换后三个indexing map分别访问哪个输入/输出。
