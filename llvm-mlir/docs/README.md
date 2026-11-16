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

自定义操作使用 `opdef-example` / `opdef-invalid` 标记，由本脚本使用加载 My dialect 的工具验证，不交给标准 `mlir-opt`。核对 ODS/C++ 片段、生成访问器与验证入口、实际打印/构造/展开及 lit 正反例。生成代码与工具进入 `artifacts/builds/mlir-op-definition/`，观察及验证日志留在 artifacts。

## 定义 IR 抽象后四章

正文位于 `compiler/ir_definition/`：`traits_interfaces.md`、`types_attributes.md`、`regions_assembly.md`、`assembly_format.md`。按章观察入口见 [06-ir-definition](../06-ir-definition/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_ir_definition.py
```

使用独立的 `irdef-example` / `irdef-invalid` 标记与注册 My dialect 的工具。维护脚本编译 ODS/C++，核对正文实际选取的关键代码、完整输入、打印往返、模型有无、效果与 DCE、类型身份、边界及 15 组失败诊断。包含普通整数的 Region 主例、多结果与空结果检查，并确认解析章的声明式格式能生成代码；不要求正文收录所有工程外壳。结果放在 `artifacts/logs/mlir-docs/<日期>-ir-definition/`。

本组示例验证的是编译器侧事实；未实现 `my.limit/scope` 的目标 lowering，也没有把作者已验证材料记成学习者已完成独立实践。

## my.add 接入导读与最小工程

学习入口为 [my-dialect](../my-dialect/README.md)，正文在 blog 的 `compiler/ir_definition/dialect_basics.md`。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_my_dialect.py
```

回归检查正文源码对应、生成方法、操作数与返回值关系、通用格式往返、错误类型/数量和未知操作。直接执行正文的 TableGen 与打印命令，核对其结果；不要求正文复制全部配置和构建步骤。字段改名验证使用 artifacts 内的作者副本，同时编译正文展开后的等价注册代码，不改动学习者 work。原始输出与源码哈希清单保存在 `artifacts/logs/mlir-docs/*-my-dialect/`。只验证编译器侧表示与约束，不执行加法。

## 操作转换与目标合法性

正文：`compiler/conversion/operation_conversion.md`；学习观察与直接命令见 [07-dialect-conversion](../07-dialect-conversion/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_conversion.py
```

构建实际模块 Pass 与对照工具，核对正文源码及完整输出、目标声明、partial/full、缺失规则和新操作未合法化的失败、动态条件、两处 use 的替换、极值/相等边界与 verifier 失败阶段。manifest 与原始结果进入 `artifacts/logs/mlir-docs/*-conversion/`。不将打印或结构验证记作目标程序数值执行；07 工程仅处理无类型变化的操作转换，类型转换见下节。

## 类型转换、混合表示与边界

正文位于 `compiler/conversion/` 的 `type_conversion.md`、`materialization.md`、`boundaries.md` 与 `advanced.md`；实际观察见 [08-type-conversion](../08-type-conversion/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_type_conversion.py
```

回归验证源码/正文一致、输入及 generic 往返、完整输出、materialization 和缺失边界规则的失败、区域重建、范围边界、analysis、递归合法性与 cast 残留检查。日志与 manifest 位于 `artifacts/logs/mlir-docs/*-type-conversion/`。1:N 仅为进阶概念；本工程未提供数值执行或性能测试，不将作者实现作为学习者任务完成记录。

## Tensor / Linalg 与编译流程导读

正文为 Tensor 三篇、Linalg 三篇和 `tutorials/pipelines/overview.md`。观察、直接命令与有限改动任务见 [09-tensor-linalg](../09-tensor-linalg/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_tensor_linalg.py
```

检查 17 份完整 IR 的正文一致性、generic 往返、buffer/循环输出、generalization、dim 折叠和五类静态失败；另外经固定版本 llc 生成本机程序，对照 109 个标量观察。数值包括不同坐标数据、旧/新值、动态窗口、归约初始值与空域，不代表性能、任意浮点误差或生命周期管理已验证。首次需要构建 llc 与 mlir_c_runner_utils，命令见实验 README。

## MemRef、Bufferization 与生命周期

正文为 MemRef 三篇，以及 `compiler/memory/` 的表示转换、One-Shot 决策和所有权三篇。直接命令、可观察输出与两个有限任务见 [10-memory-bufferization](../10-memory-bufferization/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_memory.py
```

检查 14 份正文完整输入、打印往返、9 份实际输出、冲突与不可写诊断、错误布局、缺 restrict、未知操作边界、跨函数与分支的释放结构，并对照 28 个本机标量观察。手动释放与自动释放分成两组；clone 的具体 lowering 只检查只读内容与地址关系，避免违反其中间操作的后续修改约束。日志与哈希保存在 `artifacts/logs/mlir-docs/*-memory/manifest.json`。不将结构与数值检查等同于一般内存安全证明、性能测量或学习者已完成练习。

## LLVM、CPU Lowering 与实际调用

正文为 LLVM 三篇、CPU lowering 三篇和 `tutorials/pipelines/cpu.md`。学习入口见 [11-cpu-lowering](../11-cpu-lowering/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_cpu.py
```

验证完整输入、实际阶段与 LLVM IR 输出、C 驱动对应、index 位宽、C wrapper/结果参数、33 个扩展 C 观察、正文六个数值与 JIT 42。错误路径区分 mlir-translate 的方言注册、翻译接口，以及目标文件链接符号缺失。JIT 需要固定版本 `mlir-runner`；源码与构建命令见实验入口。32 位 index 只核验转换，性能与跨目标 ABI 不在本次验证范围内。

## 分析事实与优化合法性

正文为 `compiler/analysis/` 五篇。学习入口见 [12-analysis](../12-analysis/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_analysis.py
```

构建真实 C++ 查询工具，验证支配/后支配、活跃性、别名/ModRef、调用图、常量及整数范围；包含错误保留造成缓存过期、分支合流/可达性变体、非法支配诊断与优化结构。优化前后分别编译执行，各 15 个 C 标量观察覆盖别名、内存最终值、零次循环与负数。不运行故意引入 UB 的程序，不将结构或数值测试作为所有输入证明。

## Math/Index 与 Softmax

正文为 `dialects/math/` 两篇和 `tutorials/kernels/` 的 Softmax 两篇。观察入口见 [13-softmax](../13-softmax/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_softmax.py
```

核对四份完整 IR、MathToLibm/LLVM 的 expm1 差异、32/64 位 index 转换、buffer 分配/释放结构，及两套 CPU Softmax 对 double 参考的 10 组数据/形状条件。包括错误 max 初值的数值负例、精确宽整数比较、输出哨兵、输入未修改与空形状约定。数值基线不包含 NaN/Infinity/mask 策略、计时或设备执行。

## Affine 与结构化变换

正文为 Affine 三篇与 `compiler/optimization/` 的 tiling/fusion/interchange 三篇。观察和练习见 [14-structured-optimization](../14-structured-optimization/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_structured.py
```

核对七个算法/调度 IR 的往返、实际 Affine tiling/elementwise fusion/Transform 调度、分配变化、真实依赖查询及错误绑定/乘法/排列诊断。33 组本机判据逐坐标核对裁剪、三角、余块、空域、四种逐元素实现和错误交换的数值变化。未计时，也未把当前调度脚本视为 Transform 协议已经讲完。

## Vector、Transform 与性能

正文为 Vector 三篇及优化模块的 vectorization/transform/performance。学习入口见 [15-vector-transform](../15-vector-transform/README.md)。

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_vector.py
```

验证实际 IR 往返、分块/向量化、Transform 消费与失败传播/抑制，59 组本机数值，安全的漏写 mask 反例，以及默认/允许 reassoc 的低层区别。固定 x86-64 目标汇编与三方案计时均保留：当前运行 81 个样本，正文表核对冻结的 benchmark-record.json，不以加速比作为通过阈值。源码与文档哈希记录在 *-vector/manifest.json。

## 设备、Attention 与项目源码

`validate_gpu.py` 检查 16 实验的解析往返、两类映射、NVVM 与 Host 转换，默认还编译 PTX/cubin 和 host.o；`--without-serialization` 明确只做前半段。逻辑模型和 NPU 源码检查单独标记，当前没有设备运行或性能证据。

`validate_attention.py` 检查 17 实验三种 Matmul 调度、两种 Attention 存储组织的 48 组 CPU 数值及错误 rescale 反例，保存正文/源码哈希、编译命令与输出。

`18-project-paths/observe.py --project all --check` 记录四项目的提交、LLVM 依赖、24 个源码阶段及哈希，不运行这些项目。普通 observe 模式展示各阶段的代码入口，适合有限阅读。

`validate_interfaces.py` 构建 19 工程，验证 Bufferizable 外部模型、四组 CPU 数值、InferType/Reify、RegionBranch/SCCP、标准调用/循环接口与内联，含错误边界。

`validate_ods_storage.py` 构建 20 工程，验证多组/嵌套 operands、修改分段、Properties、Type/Attr Interface 规划与参数所有权、递归名义存储。

`validate_conversion_patterns.py` 验证 21 工程的 pair 1:N、函数/call/CFG、四组加减 C 数值，以及 DRR/PDLL 相同规则与未匹配/语法错误对照。

`validate_debugging.py` 检查22工程：可重放失败、同原因缩减、Instrumentation/统计、lit/FileCheck及LSP握手，含错误数据关系反例。

`validate_bindings.py` 检查23工程官方C/Python绑定：共同的42→7变换、验证、所有权和包装生命周期、错误阶段；不执行目标函数。

`validate_bytecode_plugins.py` 检查24工程两版my.shift、字段升级与拒绝、容器版本、Linux方言/Pass插件和入口版本反例。

`validate_domains.py` 检查25工程Quant/Sparse/Shape/IRDL/Complex/TOSA有限实例，区分真实IR变换与独立Python语义模型；没有领域运行时执行或StableHLO构建。

`validate_maintenance.py` 检查26工程SCF扩展、CFG/符号维护、效果查询及标准操作有限源码链；宽index_switch的固定版本错误行为单独记录，不计为正确转换。
