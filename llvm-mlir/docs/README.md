# MLIR 文档示例验证

此目录保存 blog 示例的编写与维护工具，不是当前学习者的正式实践作业。原理正文保存在 `blog/docs/notes/compile/mlir/`，脚本读取正文中的完整模块，避免另维护一份重复示例源码。

**学习观察请从 [03-ir-api](../03-ir-api/README.md) 进入。** 它复用本目录 C++ 示例，展示实际中间 IR、use 变化、diff 和诊断；下方 `validate_*.py` 用于维护者检查，终端默认只汇总通过情况。

从 workspace 根目录运行：

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_examples.py
```

默认使用 `artifacts/builds/mlir-20.1.8/bin/mlir-opt`，输出到 `artifacts/logs/mlir-docs/<日期>-reorganized/`。可用 `--mlir-opt`、`--docs`、`--output` 覆盖路径。Python 只使用标准库。

Markdown 完整合法模块在 text fence 前写 `<!-- mlir-example: unique-id -->`。故意失败的完整模块写 `<!-- mlir-invalid: unique-id | diagnostic substring -->`；预期必须是非崩溃失败且包含对应诊断，不把任意失败都算通过。片段、示意树和伪代码不加标记。

验证内容：合法模块解析/verifier、通用打印后再解析；含 SCF 的模块转 CF 并验证输出且确认无残留 SCF；错误模块检查诊断。另检查零次 for 的 canonicalization、signed/unsigned 比较的常量化，以及教程标注的真实 CF 输出与当前工具是否一致。

manifest 记录工具版本、源页/行号、示例哈希、命令与检查结果。输入、各阶段输出与 stderr 保存在同一产物目录。没有编译或执行机器码，未测性能，未运行整个 LLVM 测试套件；用户的阅读/实践状态也不由该脚本决定。

正式实践仍按 blog 学习路径，在阅读和讨论之后另行安排。

## C++ IR API 章节

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_ir_api.py
```

使用现有 LLVM/MLIR 20.1.8 构建树的 CMake 配置与库，构建 `ir_api/` 中的独立 C++ 程序。当前固定使用本工作区的 `/usr/bin/clang`、`clang++` 和 Ninja；不重新构建整个 LLVM。程序与生成物分别进入 `artifacts/builds/mlir-ir-api-docs/` 和 `artifacts/logs/mlir-docs/<日期>-ir-api/`。

脚本从 `compiler/transforms/ir_api.md` 提取完整 MLIR 输入，检查所有标记 C++ 片段与实际源码一致，核对加零消除与新乘法创建、use/user 区别、未匹配输入、函数构造、映射克隆及两项 verifier 失败。manifest 保存源码与正文哈希、版本、命令和检查结果。

可以查看保存的输入、输出和诊断，再手动运行已构建的 `ir-api-demo MODE input.mlir`。支持 `inspect`、`zero`、`rewrite`、`build`、`clone`；`bad-dominance` 与 `bad-clone` 故意生成不合法 IR，输出诊断并返回 2。输入限定为具有单 Block 的 `@twice : (i32) -> i32`，且保留演示用新函数名。它是原理复现程序，尚未封装为 Pass。

`trace-one` 是新增的教学模式，只处理第一条匹配的加零，把 RAUW 前后与 erase 后的 IR、使用计数和使用槽位打印到 stderr，最终合法模块打印到 stdout。`03-ir-api/observe.py` 将它们组织为分步观察输出。

实际执行的是修改 IR 的 C++ 工具；本检查不 lower 或执行生成函数的机器码，不测试性能。配套源码已由编写者验证，不代表学习者已经完成下一阶段实践。

## Pass 与 pipeline 章节

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_passes.py
```

从 `compiler/transforms/passes.md` 提取例子，核对正文显示的输出、CSE/canonicalize 的组合、函数与嵌套 module 的选择范围、关闭多线程时的日志顺序，以及错误锚点和主动失败后的行为。结果放在 `artifacts/logs/mlir-docs/<日期>-passes/`，其中 manifest 记录命令、正文哈希、工具版本与检查结果。

这是章节编写者的复现检查，不是新增的学习者结业任务；不执行机器码，也不把源码摘录当成独立 C++ 工程编译。

## PatternRewriter 章节

正文：`blog/docs/notes/compile/mlir/compiler/transforms/rewriting.md`；进阶篇：同目录 `rewrite_drivers.md`。维护检查：

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_rewriting.py
```

构建 `rewriting/` 的 C++ 示例，核对两篇正文片段、单条规则的前后 IR 与未匹配推演、Walk/Greedy 输出与轨迹、原地更新、benefit 选择、空规则集与 fold/DCE、未匹配反例及循环规则的有界停止。生成物进入 `artifacts/builds/mlir-rewriting-docs/` 与 `artifacts/logs/mlir-docs/<日期>-rewriting/`。

需要观察时按 [配套 README](./rewriting/README.md) 直接运行工具，终端会显示实际 IR 与成功规则，而不只是通过计数。本次提供原理证据；正式的小 Pass 实验在阅读后安排。

## 小 Pass 贯通教程与维护记录

正文：`blog/docs/notes/compile/mlir/tutorials/first_pass.md`；可编辑工程与前后 IR 观察入口见 [04-small-pass](../04-small-pass/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_small_pass.py
```

核对正文源码片段、工具输出、重复应用与错误运行层级，并构建/运行工程的 lit/FileCheck 测试。产物进入 artifacts。通用写法见工作区 `writing_method.md`，旧章调整项见[章节审查](./chapter_review.md)。

## 操作定义章节

正文：`blog/docs/notes/compile/mlir/compiler/ir_definition/op_definition.md`；观察入口见 [05-op-definition](../05-op-definition/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_op_definition.py
```

自定义操作使用 `lab-example` / `lab-invalid` 标记，由本脚本使用加载 Lab dialect 的工具验证，不交给标准 `mlir-opt`。核对 ODS/C++ 片段、生成访问器与验证入口、实际打印/构造/展开及 lit 正反例。生成代码与工具进入 `artifacts/builds/mlir-op-definition/`，观察及验证日志留在 artifacts。

## 定义 IR 抽象后四章

正文位于 `compiler/ir_definition/`：`traits_interfaces.md`、`types_attributes.md`、`regions_assembly.md`、`assembly_format.md`。按章观察入口见 [06-ir-definition](../06-ir-definition/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_ir_definition.py
```

使用独立的 `irdef-example` / `irdef-invalid` 标记与注册 Lesson/Lab dialect 的工具。维护脚本编译 ODS/C++，核对四章源码片段、五份完整输入、打印往返、模型有无、效果与 DCE、类型身份、边界及 15 组失败诊断。结果放在 `artifacts/logs/mlir-docs/<日期>-ir-definition/`。

本组示例验证的是编译器侧事实；未实现 `lesson.limit/scope` 的目标 lowering，也没有把作者已验证材料记成学习者已完成独立实践。
