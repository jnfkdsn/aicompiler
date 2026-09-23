# 第一次源码阅读：用两个具体问题找到实现

这次阅读的目标是把文档中的结论接到真实代码。先构建练习，再任选下面一条路线。每次先读目标函数及必要的相邻声明，答清问题后就停；不从文件第一行开始通读，也不沿所有模板和辅助函数无限展开。

下面命令都从 workspace 根目录运行，依据本地 `upstream/llvm-project` 的 `llvmorg-20.1.8`。手写示例、生成代码、上游实现是三个不同层次，阅读时分别标清。

## 路线 A：一个 clamp 为什么会被判为非法

具体问题：`bounds(8, 7)` 与“operand 不是 i32”，分别由哪段代码拒绝？

第一站读自己已经认识的定义：

```bash
rg -n 'I32:|I32Attr:|hasVerifier' aicompiler-labs/llvm-mlir/05-op-definition/LabOps.td
rg -n 'ClampOp::verify' aicompiler-labs/llvm-mlir/05-op-definition/LabOps.cpp
```

把 ODS 字段类型约束与手写上下界检查分开。此处 `LabOps.cpp` 是课程示例源码，还不是 MLIR 框架内部。

第二站读构建生成的连接层：

```bash
rg -n 'ClampOp::verifyInvariantsImpl|ClampOp::verifyInvariants|local_type_constraint' artifacts/builds/mlir-exercise-clamp/reference/LabOps.cpp.inc
```

先看 `ClampOp::verifyInvariants`，确定它怎样连接生成检查与手写 `verify()`。再读 `verifyInvariantsImpl` 中 operand/result 检查的一段，沿相应 `local_type_constraint` 找到类型约束。只追到看清它检查了什么，不继续研究 TableGen 生成器。

第三站进入 MLIR 上游：

```bash
rg -n 'verifyOnEntrance|registeredInfo->verifyInvariants|LogicalResult mlir::verify' upstream/llvm-project/mlir/lib/IR/Verifier.cpp
```

在 `OperationVerifier::verifyOnEntrance` 中，找到通过已注册操作信息调用 `verifyInvariants` 的位置。这样便把框架的通用验证与第二站的操作专用检查连接起来。这里先不追完整的 Region 与 dominance 验证遍历。

读完只需要能写出这条链中的实际符号：框架查询注册信息 → 操作的生成验证入口 → 生成约束检查与手写验证。再指出两种非法输入分别在哪一层被拒绝。可以用 `invalid.mlir` 的实际诊断核对理解。

## 路线 B：replaceOp 怎样处理多个 use

具体问题：练习中旧结果同时用于 addi 的两个 operand 和 return，调用替换后这些引用怎样处理，旧 Op 是否还存在？

先打开 `Exercise.cpp`，确认你准备修改的 root 是什么、它有几个结果、新值从哪里来。随后定位上游函数：

```bash
rg -n 'void RewriterBase::replaceOp|replaceAllOpUsesWith|void RewriterBase::eraseOp' upstream/llvm-project/mlir/lib/IR/PatternMatch.cpp
```

先读参数为 `(Operation *op, ValueRange newValues)` 的 `RewriterBase::replaceOp`，按顺序标记：数量断言、替换结果使用、删除旧操作。再按需要查看 `replaceAllOpUsesWith` 的声明/实现，理解修改通知的入口：

```bash
rg -n 'replaceAllOpUsesWith|replaceAllUsesWith' upstream/llvm-project/mlir/include/mlir/IR/PatternMatch.h upstream/llvm-project/mlir/lib/IR/PatternMatch.cpp
```

本轮读到能回答以下问题即可：数量断言比较的是什么；多个 operand 使用是否需要由你逐个改；replaceOp 之后为什么不能再访问旧操作；它与单独调用 RAUW 的职责有什么差别。

最后用 `input.mlir` 的 `@multiple_uses` 对照实际输出，检查两个加法输入和返回值的引用关系。只看到常量出现还不足以证明替换完整。

## 留下怎样的记录

在自己的 `NOTES.md` 写三项即可：本次问题、查到的关键符号、代码怎样解释观察结果。函数名/文件路径比容易变化的固定行号更适合长期记录。

这两条路线是首次读源码的选择，不是额外结业关卡。之后遇到 pipeline 调度、driver 收敛或转换失败，再逐步扩大阅读范围。完整理解当前要修改的函数及其契约，会比同时打开许多底层文件更容易形成可复用的认识。
