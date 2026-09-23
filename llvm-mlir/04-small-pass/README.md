# 04：实现并测试一个小 Pass

原理正文：[把改写规则接入 Pass 与测试](../../../blog/docs/notes/compile/mlir/tutorials/first_pass.md)。这是作者已经实现并验证的讲解工程；你的独立修改任务在文末，当前不标记为完成。

## 先预测，再观察

从 workspace 根目录运行：

```bash
python3 aicompiler-labs/llvm-mlir/04-small-pass/observe.py
```

程序复用 `artifacts/builds/mlir-20.1.8`，增量构建 `lab-opt`，打印同一输入修改前后的 IR。比较 `%a` 的使用怎样接回参数，为什么只剩一条加法，零常量由谁清理。日志写入 `artifacts/logs/mlir-small-pass/<时间>/`，构建放在 `artifacts/builds/mlir-small-pass/`。

规则只处理 RHS 为整数零常量、无 overflow flags 的标量 i32 加法。Greedy 的 folding、常量 CSE 和 Region 简化已关闭，简单 DCE 仍会清理无用操作。`no-match.mlir` 使用活跃计算来检查规则拒绝范围，不能把其结论推广成“所有不匹配的死操作都保留”。

编辑 `input.mlir`，将零改为一，再次运行观察。也可以通过 `--input PATH` 指定其他输入；工具支持 builtin、func、arith、scf。独立输入保留在这里，生成文件留在 artifacts。

## 工程组成

| 文件 | 职责 |
|---|---|
| `LabPass.cpp` | Pattern、函数 Pass 与注册入口 |
| `lab-opt.cpp` | 注册方言和 Pass，进入 MlirOptMain |
| `CMakeLists.txt` | 链接本地 MLIR 库，生成工具 |
| `input.mlir` | 可编辑的学习输入 |
| `tests/rewrite.mlir` | 单条规则、多 use、嵌套区域、声明、重复应用 |
| `tests/no-match.mlir` | 非零、左零、i64、flags、未知 RHS 保留 |
| `tests/pipeline.test` | 注册可见性、错误锚点和未知 Pass 的拒绝 |
| `tests/lit.cfg.py` | lit 的工具替换、测试目录与 artifacts 输出路径 |

## 运行与测试

```bash
python3 aicompiler-labs/llvm-mlir/04-small-pass/observe.py --test
artifacts/builds/mlir-small-pass/lab-opt aicompiler-labs/llvm-mlir/04-small-pass/input.mlir --pass-pipeline='builtin.module(func.func(lab-remove-add-zero))' --verify-each
artifacts/builds/mlir-20.1.8/bin/llvm-lit -v aicompiler-labs/llvm-mlir/04-small-pass/tests
```

单独构建的完整 CMake 命令在正文中。测试配置默认使用本工作区路径，也支持 `llvm-lit --param build=/absolute/build --param llvm_bin=/absolute/llvm/bin`。`RUN` 行只有交给 lit 才自动执行；直接把文件交给工具时，它们是注释。

正文对应的额外维护检查：

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_small_pass.py
```

它检查正文与实际源码、输入输出对应，并运行上述 lit 测试。这里没有执行变换后函数的机器码；语义由规则的适用条件论证，FileCheck 检查预期 IR 关系，verifier 检查 IR 合法性。

## 阅读后的有限修改任务

将规则扩展为同时处理 `0+x`，其余类型和 flags 范围保持当前约定：

1. 先修改 `left_zero` 的输出期望，让测试失败，确认它确实在约束新需求。
2. 修改匹配与替换，注意选取正确的替代 operand。
3. 运行全部测试，确认右零、非零、多个 use、嵌套 Region 等情况没有退化。
4. 增加一个 `0+0` 输入，解释两侧都满足条件时选择哪一个已有值，以及为什么能终止。
5. 用几句话记录修改前后 IR、适用条件、一个拒绝输入和验证结果。

正文和现有代码没有提前完成这个扩展。完成并解释后，才作为你独立实现/修改 Pass 的阶段 B 证据；随后进入自定义 Op/ODS 与 verifier。
