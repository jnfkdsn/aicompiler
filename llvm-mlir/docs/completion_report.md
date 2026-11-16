# MLIR 后续课程交付报告

日期：2026-10-04。当前章节目录和覆盖表约定的后续内容已补齐，包含正文、导航、作者参考工程、观察入口、有限练习和验证记录。完整知识分类保留在 blog，labs 负责复现与修改；没有新增迁移页或第二套平行课程。

本次完成的是已有范围的教材与作者验证，不等同于穷举 MLIR 上游 API，也不等同于学习者已经完成阅读、独立实现或设备项目。交付不包含提交、推送或网站部署。

## 1. 连续学习主线

| 模块 | 本轮形成的学习过程 |
|---|---|
| CPU 编译与执行 | Linalg → 循环与访问 → MemRef descriptor / ABI → LLVM dialect → LLVM IR → C 调用及 JIT/AOT |
| 分析与合法性 | 支配/活跃性、别名/效果 → 缓存和失效 → 数据流 → CSE/DCE/LICM 的条件与反例 |
| 算法与结构化优化 | Math/Index → Softmax → Affine 域和依赖 → tiling/fusion/interchange → Vector/Transform → 性能解释 |
| 目标映射 | GPU 工作层次 → 内存布局和同步 → Host/Device 编译；NPU 资源、搬运及流水约束 |
| 算法及真实项目 | Matmul、Attention、在线 softmax 状态；Torch-MLIR、Triton、Triton-Ascend、AscendNPU IR 的有限源码链 |
| 框架进阶 | 自定义 Bufferization、类型/形状和区域接口、复杂 ODS/存储、1:N、DRR/PDLL、CFG 与符号维护 |
| 工具与领域扩展 | 调试缩减、回归/数值/性能方法、C/Python、Bytecode/插件；Quant/Sparse/Shape/IRDL/Complex、StableHLO/TOSA 定位 |

此前已交付的 Conversion、Tensor/Linalg、MemRef/Bufferization 仍是前置主线。新补的 SCF 多 Block/多路选择、并行归约/结果组装和资源/阶段化效果，分别接回所属模块，不成为第一阶段新增关卡。

正文按 `writing_method.md` 组织：先说明任务，沿数据或对象变化解释机制，必要代码及结果直接内嵌。环境配置和完整复现留在各实验 README。逐章的阅读组织审查见 [chapter_review.md](./chapter_review.md)；它和技术回归是两种检查，新章节的阅读体验仍等待用户反馈。

## 2. 实验与证据

下表是作者参考工程的有限检查，不把结构、数值、公式模型和硬件执行混为一种“通过”。检查数包含预期失败及对照，不是所覆盖程序或硬件数量。

| 实验 | 检查 / 范围 | 主要证据 |
|---|---|---|
| [11-cpu-lowering](../11-cpu-lowering/README.md) | 138 | 33 个扩展 C ABI 观察、6 个教程值、JIT 42；含解析/翻译/链接失败 |
| [12-analysis](../12-analysis/README.md) | 120 | 真实分析查询与失效反例；优化前后共 30 个 C 观察 |
| [13-softmax](../13-softmax/README.md) | 114 | 两种实现、10 组形状/数据条件；double 参考和错误初值反例 |
| [14-structured-optimization](../14-structured-optimization/README.md) | 137 | 实际 tiling/fusion/interchange、依赖查询；33 组 CPU 判据 |
| [15-vector-transform](../15-vector-transform/README.md) | 182 | 59 组 CPU 判据、Transform 行为、汇编与 81 个计时样本 |
| [16-gpu-execution](../16-gpu-execution/README.md) | 106 | NVVM、sm_80 PTX、cubin、Host object；无设备执行 |
| [17-matmul-attention](../17-matmul-attention/README.md) | 126 | 48 组 CPU 数值；在线 softmax 错误 rescale 的反例 |
| [18-project-paths](../18-project-paths/README.md) | 4 项目 / 24 阶段 | 固定源码、依赖与阶段哈希；未构建项目 |
| [19-extension-interfaces](../19-extension-interfaces/README.md) | 70 | Bufferizable、InferType/Reify、RegionBranch 消费；4 组 CPU 数组 |
| [20-ods-storage](../20-ods-storage/README.md) | 46 | 复杂参数组、Properties、存储所有权与 Type/Attr 接口 |
| [21-conversion-patterns](../21-conversion-patterns/README.md) | 43 | pair 1:N 的 8 个 C 结果；DRR/PDLL 实际规则与对照 |
| [22-debug-testing](../22-debug-testing/README.md) | 31 | 失败重放、同原因缩减、lit/FileCheck、统计与 LSP 握手 |
| [23-bindings](../23-bindings/README.md) | 26 | 官方 C/Python 共同 IR 修改、所有权和错误阶段 |
| [24-bytecode-plugins](../24-bytecode-plugins/README.md) | 45 | 两版方言字段升级、拒绝边界、Linux 方言/Pass 插件 |
| [25-domain-extensions](../25-domain-extensions/README.md) | 63 | Quant/Sparse/Shape/IRDL/Complex/TOSA 的 IR 证据；独立公式模型 |
| [26-ir-maintenance](../26-ir-maintenance/README.md) | 59 | 17 个范围明确的 CPU 用例、结构维护、效果查询、7 个源码入口 |

所有 11—26 工程的表列检查均通过。09/10 工程及更早阶段沿用各自已交付证据；本次最终审计没有无差别重跑全部历史实验。计时记录只说明当前配置，不能推导通用加速比。

## 3. 固定版本与复现位置

标准工具链为 LLVM `llvmorg-20.1.8`，提交 `87f0227cb60147a26a1eeb4fb06e3b505e9c7261`。构建包含 Native/NVPTX，assertions 开启、RTTI 关闭；官方 Python 绑定为同一源码构建。依赖与硬件状态见[环境矩阵](../../environments/version-matrix.md)。项目自身的 LLVM 版本由 [source_map.json](../18-project-paths/source_map.json)单独记录。

各实验 README 给出直接工具步骤、observe 与有限修改任务；[验证入口](./README.md)集中记录维护脚本。日志保存在 workspace 的 `artifacts/logs/mlir-docs/<目录>/manifest.json`，包含命令、阶段 IR、退出状态、诊断、源码/正文哈希。以下目录用于定位本次采用的证据，不作为网页外链：

| 实验 | manifest 所在目录 |
|---|---|
| 11 | `2026-10-04-060954-912574-cpu` |
| 12 | `2026-10-04-024045-059873-analysis` |
| 13 | `2026-10-04-025541-743279-softmax` |
| 14 | `2026-10-04-031057-301880-structured` |
| 15 | `2026-10-04-032803-710586-vector` |
| 16 | `2026-10-04-043247-603106-gpu` |
| 17 | `2026-10-04-041220-303455-attention` |
| 18 | `2026-10-04-050620-097861-project-sources` |
| 19 | `2026-10-04-045433-272378-interfaces` |
| 20 | `2026-10-04-050220-242921-ods-storage` |
| 21 | `2026-10-04-050959-146831-conversion-patterns` |
| 22 | `2026-10-04-060748-649336-debug-testing` |
| 23 | `2026-10-04-052749-583326-bindings` |
| 24 | `2026-10-04-060749-817677-bytecode-plugins` |
| 25 | `2026-10-04-060750-013214-domain-extensions` |
| 26 | `2026-10-04-055623-076949-ir-maintenance` |

## 4. 最终文档检查

- VitePress 全站构建通过；MLIR/TableGen 语法高亮回退为普通文本的提示不影响内容呈现。
- MLIR 全部页面及三篇项目延伸共 140 页，777 处正文站内链接无目标缺失。
- 渲染后的导航、正文链接及 1294 处锚点引用无缺失；新增目录表格已检查并修正断行。
- 280 处固定 LLVM 20.1.8 源码引用，以及全部所引 GitHub 仓库文件路径，均与本地相应源码/实验仓库对应。这里检查的是文件路径，不表示新文件已经推送到 GitHub。
- 两个仓库的 `git diff --check` 通过。导航、覆盖表和学习路径同步，但没有把作者验证写为用户已掌握。
- 当前文件与所选 manifest 做哈希核对。分析及 Math 模块的两个目录页在各批验证后补入导航；最终站点审计另存正文快照。实验实现及维护脚本与所选证据一致。

最终审计快照保存在 `artifacts/logs/mlir-docs/*-completion/manifest.json`，同时保存站点构建日志和链接检查结果。

## 5. 明确保留的验证边界

1. **GPU/NPU**：当前环境没有设备执行和性能证据。GPU 已实际生成 PTX/cubin 与 Host object；不能据此宣称 kernel 在设备上正确运行。NPU 和四个实际项目以固定源码追踪为证据。
2. **SCF 固定版本限制**：LLVM 20.1.8 的 `IndexSwitchLowering` 将 selector 缩为 i32，宽标签 `4294967296` 可能走错分支；此观察单列为限制。CPU 正确性用例使用明确范围的标签。多出口 `execute_region` 的 One-Shot Bufferization 支持限制也已记录。
3. **目标与领域范围**：SCF parallel/forall 的 CPU 测试来自串行参考 lowering。StableHLO 是定位篇，未构建；稀疏运行时、量化网络执行、复数 ABI、通用动态形状运行时尚未验证。Python 公式模型与真实 MLIR 执行分开。
4. **原生工具集成**：外部工程需要匹配 LLVM 的 assertions/RTTI 等配置。插件入口版本不保证跨版本 C++ ABI；固定 mlir-opt 错误插件路径的未消费 Error 行为已有记录，拒绝用例采用显式处理错误的宿主。
5. **数值与性能**：Softmax/Attention 的输入条件、误差和特殊值边界见各章，不宣称所有 dtype、mask、NaN/Infinity 或任意规模都已覆盖。目标项目的完整 FlashAttention 与设备优化保留为后续独立实践。

这些边界已经在相关正文与实验中说明。覆盖表中的长期 D3/D4 项继续服务于研究任务，不通过追加大量入门前置来假装一次完成全部工程能力。

## 6. 学习者接下来做什么

按最后一次反馈，IR 定义已经基本理解，后续章节尚未确认读完。建议继续 Conversion 的操作及最小类型转换，然后读编译流程导读 → Tensor/Linalg → MemRef/Bufferization → CPU 执行链。先完成这一条路径，再用 Softmax 或 Matmul 选取需要的分析与优化。

每次完成一个机制后，在相应实验 README 中选一个有限修改任务：先写出预期 IR 或结果，再修改并观察差异，最后解释成功与失败的条件。参考工程已经完整实现，独立任务保留给学习者；不需要为了“课程完成”一次读完所有扩展。
