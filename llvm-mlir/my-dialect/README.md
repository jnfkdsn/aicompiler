# 从 my.add 开始开发 Dialect

本目录保留最小阶段：让自己的 `my-opt` 认识、验证并打印 `my.add`，不执行整数加法。后续定义机制进入 [05-op-definition](../05-op-definition/README.md) 和 [06-ir-definition](../06-ir-definition/README.md)，仍使用 `my` 教学方言；不在这里另开一套重复课程。

中文讲解见 [第一篇教程（blog 仓库）](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/mlir/compiler/ir_definition/dialect_basics.md)。本地对应路径是 `blog/docs/notes/compile/mlir/compiler/ir_definition/dialect_basics.md`；新文件需要分别推送到两个仓库后，网页链接才可访问。

## 首次学习：逐步构建并观察

Blog 第一篇已内嵌各步产物、生成的 C++ 摘录与输出。下面是从 workspace 根目录执行的命令清单，在同一个 Bash 终端按顺序运行。使用已有 LLVM/MLIR 20.1.8、Clang 和 Ninja，不重建 LLVM。

```bash
MYLAB_SRC="$PWD/aicompiler-labs/llvm-mlir/my-dialect/stages/01-minimal"
MYLAB_LLVM="$PWD/artifacts/builds/mlir-20.1.8"
MYLAB_BUILD="$PWD/artifacts/builds/my-dialect-01-steps"
cmake -S "$MYLAB_SRC" -B "$MYLAB_BUILD" -G Ninja \
  -DMLIR_DIR="$MYLAB_LLVM/lib/cmake/mlir" \
  -DLLVM_DIR="$MYLAB_LLVM/lib/cmake/llvm" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++ \
  -DCMAKE_C_COMPILER=/usr/bin/clang

# 只生成四份 C++ 片段；可加 --verbose 查看实际生成命令
cmake --build "$MYLAB_BUILD" --target MyIncGen -j2
# 编译 MyOps.cpp，得到对象文件并归档为 libMyIR.a
cmake --build "$MYLAB_BUILD" --target MyIR -j2
# 编译工具入口并链接得到 my-opt
cmake --build "$MYLAB_BUILD" --target my-opt -j2
# 直接读取、验证、打印
"$MYLAB_BUILD/my-opt" "$MYLAB_SRC/input.mlir"
"$MYLAB_BUILD/my-opt" "$MYLAB_SRC/input.mlir" --mlir-print-op-generic
```

生成物位于 `artifacts/builds/my-dialect-01-steps/`。每一步具体生成哪些代码、如何接入下一步，见第一篇第 4—7 节。已完成的步骤会报告 `no work to do`，属于正常的增量构建。

熟悉过程后，可用快捷脚本重跑并保存日志：

```bash
python3 aicompiler-labs/llvm-mlir/my-dialect/observe.py
```

脚本使用单独的 `my-dialect-01` 构建目录，读取同一份源码。它展示 ODS、生成访问器、输入、两种打印并验证往返；首次学习以分步命令为入口。

## 本步文件

| 文件 | 角色 |
|---|---|
| [MyOps.td](stages/01-minimal/MyOps.td) | 声明 my dialect、my.add 的两个输入和一个结果及文本格式 |
| [MyOps.h](stages/01-minimal/MyOps.h) | 包含生成的 Dialect/Op 声明 |
| [MyOps.cpp](stages/01-minimal/MyOps.cpp) | 包含生成实现，在 Dialect 初始化时注册操作 |
| [my-opt.cpp](stages/01-minimal/my-opt.cpp) | 向工具提供 My/Func dialect 注册表 |
| [CMakeLists.txt](stages/01-minimal/CMakeLists.txt) | 生成四个 inc 文件，构建 MyIR 库并链接工具 |
| [input.mlir](stages/01-minimal/input.mlir) | 本轮贯穿使用的完整输入 |

分步构建的 `.inc` 位于 `artifacts/builds/my-dialect-01-steps/`（快捷脚本使用 `my-dialect-01/`）。请修改 `.td` 或手写 C++，不修改生成物。首次只追 AddOp、getLhs/getRhs、build/parse/print/verifyInvariants 的位置，不读完生成文件。

## 轮到你修改

任务：[01：重命名一个 ODS 字段，观察生成接口](tasks/01-rename.md)。只改一个字段及其格式引用，计算语义不变。

任务单提供直接复制、配置、生成、构建和运行命令；也可在熟悉过程后使用 `observe.py --prepare-task` 与 `observe.py --task` 两个快捷入口。

创建副本不会覆盖已有目录。`work/` 是你的源码工作区，可自行提交进 lab 仓库；其中不放构建产物。参考和练习使用独立 build 目录。任务完成后告诉我，我会检查改动与解释；不会把准备好的参考工程记为你已完成练习。

## 阶段版本与网页链接

`stages/01-minimal/` 保存导读对应的完整参考版本。它与 05、06 工程各自独立构建，按章节提供不同能力，不在同一程序里链接多份 MyDialect 定义。参考版本允许修复错误，但不把后续能力叠进导读。发布后若需要严格固定某版，可使用 GitHub 的 commit permalink；`main` 链接始终指向分支最新内容。

Blog 内部页面用站内相对链接；跨仓库源码用 `https://github.com/jnfkdsn/aicompiler/blob/main/...`，目录用 `tree/main/...`。不能在网页上用 `../aicompiler-labs/` 去寻找本地兄弟目录。生成文件和日志不上传，正文保留关键输出，完整内容在本地复现。

## 作者回归

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_my_dialect.py
```

检查正文与源码、解析/打印往返、错误类型/数量、未知操作及改名任务的预期效果。作者检查在 artifacts 内另建副本，不修改你的 `work/`。固定版本为 LLVM `llvmorg-20.1.8`，结果属于编译器侧证据。
