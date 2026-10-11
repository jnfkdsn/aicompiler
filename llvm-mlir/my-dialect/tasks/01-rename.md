# 任务 01：改一个字段，沿生成链观察结果

先读第一篇教程并运行参考观察。目标是确认 ODS 的命名如何变成 C++ API，同时区分字段名和 IR 中的 SSA 名称。

## 准备自己的副本

从 workspace 根目录运行：

```bash
MYLAB_SRC="$PWD/aicompiler-labs/llvm-mlir/my-dialect/stages/01-minimal"
MYLAB_WORK="$PWD/aicompiler-labs/llvm-mlir/my-dialect/work/01-rename"
mkdir -p "$(dirname "$MYLAB_WORK")"
if [ ! -e "$MYLAB_WORK" ]; then
  cp -R "$MYLAB_SRC" "$MYLAB_WORK"
fi
```

打开 `aicompiler-labs/llvm-mlir/my-dialect/work/01-rename/MyOps.td`。上述命令遇到已有副本会保留，不覆盖你的改动。

## 你来做的修改

把 AddOp 的第一个 operand 字段名从 `lhs` 改成 `left`，并同步更新 `assemblyFormat` 中对该字段的引用。其余字段与语义保持不变，不修改输入文件中的 `%a`，不编辑任何 `.inc`。

运行前先预测三件事：生成的访问器会怎样变化；输入文本是否需要改；正常打印的 IR 是否变化。预测写几行即可。

```bash
MYLAB_LLVM="$PWD/artifacts/builds/mlir-20.1.8"
MYLAB_TASK_BUILD="$PWD/artifacts/builds/my-dialect-01-task"
cmake -S "$MYLAB_WORK" -B "$MYLAB_TASK_BUILD" -G Ninja \
  -DMLIR_DIR="$MYLAB_LLVM/lib/cmake/mlir" \
  -DLLVM_DIR="$MYLAB_LLVM/lib/cmake/llvm" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++ \
  -DCMAKE_C_COMPILER=/usr/bin/clang
cmake --build "$MYLAB_TASK_BUILD" --target MyIncGen -j2
rg -n 'getLeft|getLhs|getRhs' "$MYLAB_TASK_BUILD/MyOps.h.inc"
cmake --build "$MYLAB_TASK_BUILD" --target my-opt -j2
"$MYLAB_TASK_BUILD/my-opt" "$MYLAB_WORK/input.mlir"
```

对照原始 `artifacts/builds/my-dialect-01-steps/MyOps.h.inc`（若用快捷脚本构建参考版本，则在 `my-dialect-01/`）。要同时检查：工程仍能构建，访问器名称符合预测，输入仍可读且往返不变。仅构建成功不足以说明字段真的改了。

补充：若想检查修改后的打印往返，可按教程第 7 节运行，把命令中的构建与源码变量分别换成 `MYLAB_TASK_BUILD`、`MYLAB_WORK`。熟悉各步后也可用 `observe.py --task` 统一运行并检查往返。

<details>
<summary>如果 TableGen 报错</summary>

先核对 assemblyFormat 的 `$变量` 是否仍指向已声明字段。ODS 的字段名、C++ 访问器、文本输入中的 SSA 名称分属不同位置，逐项对照，不要批量改动所有带相似字样的文件。

</details>

## 交给我审阅的内容

保留修改后的 `.td`，在同目录写一个短 `NOTES.md`：修改点、预测与实际观察，以及“字段名和 SSA 名称有什么不同”。告诉我任务完成即可；无需复制大段生成文件到笔记里。

下一步再把这份自定义 IR 接到已学过的 Pattern/Pass，将 my.add 改写成 arith.addi。当前任务不要求提前实现 lowering。
