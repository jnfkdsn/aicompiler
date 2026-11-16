# LLVM / MLIR 实验

本目录服务于“预测 → 运行观察 → 修改 → 解释结果”的学习流程。blog 保存原理与源码解释，实验目录保存可编辑输入、学习步骤和程序；生成的 IR、诊断和日志保存在 workspace 的 `artifacts/`。

| 入口 | 用途 |
|---|---|
| [my-dialect](./my-dialect/README.md) | my.add 接入导读的最小参考版本、生成代码观察与字段改名任务 |
| [动手练习](./exercises/README.md) | 两个独立任务：clamp 简化与按行 Softmax；工程已提供，关键实现留作 TODO |
| `01-ir-basics/sum_positive.mlir` | 已独立编写的基础 IR 程序 |
| `02-pass/twice.mlir` | Pass 与 pipeline 的个人实验输入 |
| [03-ir-api](./03-ir-api/README.md) | 分步观察 RAUW、erase、完整改写、支配错误和克隆映射，可修改输入验证预测 |
| [04-small-pass](./04-small-pass/README.md) | 完整函数 Pass 工程、前后 IR 观察与 lit/FileCheck；阅读后独立扩展左侧加零 |
| [05-op-definition](./05-op-definition/README.md) | 定义 my.clamp，观察 ODS 生成 API、builder、验证、打印与 Pass 展开 |
| [06-ir-definition](./06-ir-definition/README.md) | 观察通用接口消费、Type/Attr 参数与存储、Region 传值及打印验证 |
| [07-dialect-conversion](./07-dialect-conversion/README.md) | my.clamp 转 arith，观察目标合法性、partial/full、动态条件与失败；可修改目标配置 |
| [08-type-conversion](./08-type-conversion/README.md) | range 到 i32，观察函数/调用/Region、materialization、cast 清理及失败对照；包含有限修改任务 |
| [09-tensor-linalg](./09-tensor-linalg/README.md) | Tensor 值/形状/切片与 Linalg 映射、广播、归约、DPS；展示 buffer/循环输出并执行小规模数值对照 |
| [10-memory-bufferization](./10-memory-bufferization/README.md) | MemRef 布局与别名、One-Shot 决策及所有权释放；分析/转换输出、数值观察与两个有限修改任务 |
| [11-cpu-lowering](./11-cpu-lowering/README.md) | Linalg→循环→LLVM、描述符/C ABI、目标文件与 JIT；连续/非连续输入、空域和返回存储观察 |
| [docs](./docs/README.md) | 文档维护工具及经过编译验证的共享示例代码；`validate_*.py` 的通过计数是回归证据 |

课程配套代码的回归检查不替代学习实验。学习入口应展示输入、关键中间状态、输出与解释线索，并提供有限的修改任务。PatternRewriter 原理示例与小 Pass 工程沿用这个组织方式。

## 现在想动手时

已完成基础原理和 Softmax 阅读后，动手主线是 [clamp 简化](./exercises/01-clamp-simplify/README.md) → [按行 Softmax](./exercises/02-softmax/README.md)。后者只需填写一个 MLIR 文件中的两个 TODO，检查会展示输入、实际输出与参考结果。其他编号目录是完整参考实验，不要求依次运行；遇到具体问题再查对应目录。

`my-dialect`、`05`、`06` 分别提供最小接入、基础操作和扩展机制的 `my` 方言版本。它们独立构建；工具都叫 `my-opt`，需要按 README 使用各自的构建路径。`06` 不再链接 `05` 的方言库，避免重复定义。`04` 只变换标准 arith 操作，其 `lab-opt` 名称是工具名，不是另一个教学方言。`docs/` 保存维护工具，`exercises/` 保存留给学习者实现的任务。

clamp 练习只需填写一段匹配/改写逻辑并补用例，构建和注册可以复用。任务中的 [源码阅读路线](./exercises/01-clamp-simplify/SOURCE_READING.md) 从生成验证入口或 replaceOp 的一个具体问题进入上游实现。

- [12-analysis](./12-analysis/README.md)：支配、活跃性、别名/效果、缓存失效、常量/范围传播及 CSE/LICM；打印真实结论和前后 IR，支持优化前后的 C 数值对照。
- [13-softmax](./13-softmax/README.md)：Math/Index 转换、四阶段与按行 Softmax、double 参考与形状/数值边界；未测性能，不把逻辑访问变化当加速比。
- [14-structured-optimization](./14-structured-optimization/README.md)：Affine 域/访问/依赖、真实分块/融合/交换，包含合法结果与错误重排数值反例。

- [15-vector-transform](./15-vector-transform/README.md)：向量值/边界/收缩、自动向量化与 Transform 协议；本机数值、真实汇编及冻结配置的计时对照。

- [16-gpu-execution](./16-gpu-execution/README.md)：并行映射、地址空间、同步/异步及 Host/Device 产物；编译、逻辑模型和设备运行分开记录。
- [17-matmul-attention](./17-matmul-attention/README.md)：Matmul 分块/展开、物化与在线 Attention，含 double 参考和错误递推反例。
- [18-project-paths](./18-project-paths/README.md)：固定 torch-mlir、Triton、Triton-Ascend、AscendNPU-IR 的有限源码链，打印实际入口、保存快照证据。

- [19-extension-interfaces](./19-extension-interfaces/README.md)：自定义 Bufferization、类型/尺寸、RegionBranch 的真实消费者及调用/循环/内联边界。

- [20-ods-storage](./20-ods-storage/README.md)：复杂参数组、Properties、参数复制与共享身份、Type/Attr 接口消费和递归存储。

- [21-conversion-patterns](./21-conversion-patterns/README.md)：pair 1:N 跨边界转换、CPU 数值与 DRR/PDLL 规则对照。

- [22-debug-testing](./22-debug-testing/README.md)：失败重放、IR缩减、Instrumentation、lit/FileCheck和LSP协议。
- [23-bindings](./23-bindings/README.md)：官方C/Python两条对象操作链及生命周期。
- [24-bytecode-plugins](./24-bytecode-plugins/README.md)：方言字段升级、容器版本和原生插件。
- [25-domain-extensions](./25-domain-extensions/README.md)：Quant/Sparse/Shape/IRDL/Complex/TOSA的有限表示与转换观察。
- [26-ir-maintenance](./26-ir-maintenance/README.md)：SCF扩展协议、CFG/符号维护、效果实例和有限源码链；17个CPU正确范围用例与独立版本限制记录。

全部已规划内容的交付范围、证据和未验证边界见[交付报告](./docs/completion_report.md)。文档完成不表示个人练习已完成。
