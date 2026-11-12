# 23：从 C 与 Python 操作同一份 IR

主线：解析 answer 的 20+22 → canonicalize 得到常量42 → 在return之前插入常量7并修改operand → 再清理死常量。两条接口路径输出一致。目标是理解嵌入工具与所有权，不是从C调用编译后的answer。

## 固定依赖

LLVM llvmorg-20.1.8（87f0227cb60147a26a1eeb4fb06e3b505e9c7261），assertions ON、RTTI OFF。官方 Python bindings 使用 Python 3.12，独立 venv，固定依赖见 python-requirements.txt。源码下构建 MLIRPythonModules；不安装同名第三方 mlir 包。

在已有工具链上补建，workspace 根目录示例：

```bash
python3 -m venv artifacts/venvs/mlir-python20
artifacts/venvs/mlir-python20/bin/python -m pip install \
  -r aicompiler-labs/llvm-mlir/23-bindings/python-requirements.txt
cmake -S upstream/llvm-project/llvm -B artifacts/builds/mlir-20.1.8 \
  -DMLIR_ENABLE_BINDINGS_PYTHON=ON \
  -DPython3_EXECUTABLE="$PWD/artifacts/venvs/mlir-python20/bin/python" \
  -DPython_EXECUTABLE="$PWD/artifacts/venvs/mlir-python20/bin/python"
cmake --build artifacts/builds/mlir-20.1.8 --target \
  MLIRPythonModules MLIRCAPIIR MLIRCAPIArith MLIRCAPIFunc MLIRCAPITransforms -j 2
```

配置命令沿用已有 build 的 MLIR/Ninja/LLVM 选项；全新构建应先按环境文档配置，不把上述增量命令当完整初始参数。

## 直接运行

```bash
cmake -G Ninja -S aicompiler-labs/llvm-mlir/23-bindings \
  -B artifacts/builds/mlir-bindings \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=/usr/bin/clang \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++
cmake --build artifacts/builds/mlir-bindings -j 2
artifacts/builds/mlir-bindings/c-api
PYTHONPATH="$PWD/artifacts/builds/mlir-20.1.8/tools/mlir/python_packages/mlir_core" \
  artifacts/venvs/mlir-python20/bin/python \
  aicompiler-labs/llvm-mlir/23-bindings/bindings.py
```

观察 after fold 的42和 after replacement 的7；ret改变引用，第二次canonicalize删除42。C程序按拥有关系清理，不单独销毁已插入Block的seven。

```bash
python3 aicompiler-labs/llvm-mlir/23-bindings/observe.py
python3 aicompiler-labs/llvm-mlir/docs/validate_bindings.py
```

还会运行 lifetime.py：显式erase后旧包装被拒绝；module离开默认Context作用域后仍可验证。errors.py区分文本解析与pipeline解析异常。不执行C悬空指针访问，也不声称任意外部Pass的删除都能被Python包装完整检测。

## 有限练习

1. 在脚本副本中把7变为命令行整数，预测并观察IR。
2. 在第一次Pass之后重新取得return，再改为11；说明为何不保存可能已被替换的旧常量句柄。
3. 增加一个缺失Pass名称的输入，保留异常阶段和诊断，避免宽泛except后继续使用失败结果。

两种接口的数值42/7来自编译器折叠和IR构造；本工程未生成和运行目标机器函数。
