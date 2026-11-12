# 24：Bytecode 升级与插件

my.shift 表示i32输入加有符号i32范围内的偏移（属性用i64保存），按i32模运算。v1只接受bias，v2只接受offset；两工具用同一LLVM20.1.8编译。当前升级将旧字段改名，未来版本明确拒绝。

## 直接观察

```bash
cmake -G Ninja -S aicompiler-labs/llvm-mlir/24-bytecode-plugins \
  -B artifacts/builds/mlir-bytecode-plugins \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=/usr/bin/clang \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++
cmake --build artifacts/builds/mlir-bytecode-plugins -j 2
artifacts/builds/mlir-bytecode-plugins/my-opt-v1 \
  aicompiler-labs/llvm-mlir/24-bytecode-plugins/v1.mlir \
  --emit-bytecode -o artifacts/builds/mlir-bytecode-plugins/old.mlirbc
artifacts/builds/mlir-bytecode-plugins/my-opt-v2 \
  artifacts/builds/mlir-bytecode-plugins/old.mlirbc
```

输出offset=5；加--my-lower-shift --canonicalize得到42。直接把v1文本交给v2不会有版本升级，预期被verifier拒绝。

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/24-bytecode-plugins/v2.mlir \
  --load-dialect-plugin="$PWD/artifacts/builds/mlir-bytecode-plugins/MyPlugin.so" \
  --load-pass-plugin="$PWD/artifacts/builds/mlir-bytecode-plugins/MyPlugin.so" \
  --pass-pipeline='builtin.module(my-plugin-mark)'
python3 aicompiler-labs/llvm-mlir/24-bytecode-plugins/observe.py
python3 aicompiler-labs/llvm-mlir/docs/validate_bytecode_plugins.py
```

插件实际添加module属性my.plugin_seen。原生插件采用Linux共享模块，由同一构建的宿主导出MLIR符号；assertions和RTTI配置匹配。并非跨版本/平台二进制兼容测试。

BadPlugin故意使用不兼容入口版本；plugin-check通过PassPlugin::load检查，并消费Expected错误。固定assertions宿主的命令行错误路径可能因未消费Expected而中止，所以负例使用明确处理Error的探针，不把中止当正常拒绝证据。

## 观察边界与练习

Bytecode容器版本与my方言版本各自独立。--emit-bytecode-version=0仍写当前offset；这不是把新方言降级到v1。普通属性字典用于隔离本次版本主题；Properties/custom Type编码演化还需相应兼容decoder。

1. 在副本中将bias改为-5，预测两版本lower后的常量。
2. 在v2副本中同时写bias与offset，解释为何必须拒绝而非随意选一个。
3. 去掉加载Pass的选项，保留Dialect插件，观察为什么文本可读但pipeline名称不可用。

这些结果来自编译器解析/升级/折叠和插件执行，没有运行目标kernel。
