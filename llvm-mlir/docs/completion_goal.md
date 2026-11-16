# MLIR 后续教程持续目标：交付已完成

开始：2026-10-04。用户明确要求使用 goal 模式生成后续 MLIR 全部内容。规范范围为 blog 的 `chapter_plan.md` 与 `coverage.md`，写法遵循 workspace `writing_method.md`。本文件是工作清单，不替代公开目录，也不记录用户已经掌握。

## 完成条件

- 已规划主题均有对应正文或职责明确的参考篇，主线文章沿完整案例推演，不用目录/术语表冒充正文。
- 每批同步章节导航、覆盖表、逐章阅读审查与适当技术证据。
- 可运行部分按固定版本验证，提供观察与有限练习；硬件和特定依赖不具备时如实标明验证层次，完成可做的源码核对与编译检查。
- 可选专题按已约定深度展开；不以穷举 MLIR 全部方言/API、完成所有 D4 研究任务或替学习者完成练习作为终点。
- 对已有章节需要连接的部分进行必要修正，不在此目标中无差别重写全部旧文。
- 不提交、推送或部署，不更改全局记忆。

## 按依赖交付

| 批次 | 范围与目录 | 状态 |
|---|---|---|
| 0 | Conversion、Tensor/Linalg、MemRef/Bufferization 主线 | 已交付；见原有验证与审查 |
| 1 | LLVM 三篇、CPU lowering 三篇、Linalg→CPU 贯通 | 已完成：138 项检查、C 调用和 JIT、站点通过 |
| 2 | 分析：支配/活跃性/调用、别名与依赖、缓存失效、数据流、CSE/DCE/LICM | 已完成：五篇、120 项检查、30 个前后 C 观察、站点通过 |
| 3 | Math/Index；归约与 Softmax 基线、数值验证 | 已完成：四篇、114 项检查、两实现/10 组输入、站点通过 |
| 4 | Affine、tiling、fusion、interchange、Vector、Transform、性能解释 | 已完成：4A/4B 共十二篇；137/182 项检查，含真实性能记录 |
| 5 | GPU 方言、并行层次、设备内存/布局、同步异步与 Host/Device；NPU 约束 | 已完成：八篇、16 实验106项、NVVM/PTX/cubin/Host object；设备运行不可用，站点通过 |
| 6 | Matmul/Attention；固定版本前端与 Triton/AscendNPU IR 有限源码链 | 七篇已完成，17 实验126项/48数值，18扩为四项目24阶段；新增Triton-Ascend桥接源码篇 |
| 7 | 自定义 BufferizableOpInterface、类型/形状/区域接口、复杂 ODS/存储、1:N conversion 与声明式改写 | 已完成七篇：19实验70项、20实验46项、21实验43项；站点12.76s通过 |
| 8 | 调试/最小复现、测试与数值性能方法、C/Python API、bytecode/版本/插件；quant/sparse/shape/IRDL/complex 定位 | 已完成：八篇工具正文与六篇领域正文；22—25工程31/26/45/63项，有限源码篇由26工程覆盖 |
| 9 | 全目录覆盖审计、链接和站点检查、遗漏主题补全、交付报告 | 已完成：五篇连接/源码正文、26工程59项（17个范围明确CPU用例）；140页/777链接及渲染锚点审计、最终站点与报告 |

## 持续约定

章节按职责归档，阅读按依赖链接；教学自定义方言使用 `my`。Blog 独立可读，关键代码与结果内嵌；lab 承担工程、直接命令、观察和练习。性能结论必须有对应配置与实测，源码推演和硬件执行分开。没有用户反馈的新章节不记为已读。

## 最近工作

2026-10-04：目标已创建，正在准备第 1 批。主例采用已有矩阵加法，并进一步演示动态/非连续 MemRef 的 C 调用，以连接上一批的布局与生命周期。

2026-10-04：第 1 批七篇已生成，138 项检查包含 33 个扩展 C 观察、六个教程值与 JIT 42；458 处站内链接无缺失，站点构建通过。补建 mlir-runner。开始第 2 批分析章节备课；本地除 llvm-project 外的 upstream 项目目录尚无 Git checkout，真实项目章节后续需取得固定版本源码依据。

2026-10-04：第 2 批五篇与 12-analysis 已完成。真实查询、缓存反例、常量/范围与 CSE/LICM 对照共 120 项通过，站点通过。开始第 3 批 Math/Index 与 Softmax；用户新增章节的阅读状态仍未知。

2026-10-04：第 3 批四篇和 13-softmax 已完成，114 项通过，510 处站内链接无缺失，站点构建通过。第 4 批开始，按 Affine/结构化变换与 Vector/Transform/性能两段写作。

2026-10-04：第 4A 批 Affine 三篇、tiling/fusion/interchange 三篇已生成；14 实验 137 项检查、33 组本机判据通过。真实依赖反例有 4 与 102 的结果差异。接续第 4B 批 Vector 三篇、自动向量化、Transform 协议与计时性能解释。

第 4A 最终状态：137/137，manifest 2026-10-04-031057-301880-structured；站点通过，531 处链接无缺失。第 4B 已开始查固定版本 Vector/Transform 源码，尚未写正文或工程。

2026-10-04：第 4B 六篇与 15 实验已完成，182 项检查包含 59 组本机判据、81 组计时、Transform 消费与失败语义。目录/覆盖表已同步，开始第 5 批设备执行。

第 4B 最终状态：182/182，manifest 2026-10-04-032803-710586-vector；站点通过，565 处链接无缺失。开始 GPU/目标源码核验；当前 PATH 无 nvidia-smi/npu-smi，但有 ptxas，尚未确定设备可用性。

第 5 批检查点：16-gpu-execution 已有 launch/shared/async/parallel/forall/map-forall 六份 IR 与 models.py。parallel/forall→launch、outlining 和 GPU→NVVM 已用旧 mlir-opt 验证。Host gpu-to-llvm 保留 launch_func，真正启动调用由 GPU LLVM translation + gpu.binary 完成，勿提前声称已变成 mgpuLaunchKernel。async 已添加 host_register/unregister；共享 private attribution 实际是 alloca，不能机械写成 ptr<5>。

工具链为同一 20.1.8 增加 Native;NVPTX，触发较多依赖重建；运行中 exec session 58225（cmake --build ... --target mlir-opt mlir-translate llc -j 2），最近约 700/3769。系统 CUDA 12.4.131 的 ptxas 可用；/usr/lib/wsl/lib/nvidia-smi -L 报 GPU access blocked by operating system，无设备执行证据。三个公开仓库浅克隆已启动，供后续固定源阅读：AscendNPU-IR 查询HEAD37c6ebc33d1789500014e6a7b2b62164b3cb566b，torch-mlir查询HEAD528d3dcb9a2288743b62df9f4937b1689787e38a，Triton v3.2.0标签9641643da6c52000c807b5eeed05edaec4402a67；需以克隆后rev-parse最终确认。

2026-10-04 第 5/6 批检查点：GPU八篇均写完，87/87不含序列化通过；NVPTX构建58225约3365/3769。Matmul/Attention三篇和17实验126/126（48组数值，反例28→40）通过。Torch/Triton/HIVM三条源码篇已写，18阶段快照通过，未执行项目。导航已连接，待站点和链接复核、PTX/cubin收尾。

第5/6批站点13.77s通过，618处站内链接无缺失，git diff --check两仓通过。待完成NVPTX序列化（58225约3694/3769）；Triton-Ascend公开仓库ls-remote会话45805尚未返回，后续可用triton-lang新镜像或GitCode核对，避免混用NVIDIA路径。

第5批最终验证：NVPTX构建完成，106/106通过，manifest 2026-10-04-043247-603106-gpu；实际sm_80 PTX、CUDA12.4 cubin与Host object。shared编译报告12registers/16bytes smem/无spill；Host使用mgpuModuleLoadJIT。无GPU运行。第7批备课开始：自定义bufferization、类型/shape/region接口、复杂ODS/存储、1:N和声明式改写。

第7批备课：读者已理解旧/新Tensor与OneShot决策；主例my.add_one(x,outs)以逐元素+1说明输入read、目标write/不读初值、结果alias目标Equivalent、旧值存活迫使新分配。19-extension-interfaces已建立独立my方言工程，生成InferType（由SameOperandsAndResultType）与手写Reify shape接口、外部Bufferizable模型；正在首次构建调试，正文尚未写。后续扩展范围：类型/形状与RegionBranch/Call接口消费，复杂ODS参数存储，1:N与声明式改写，逐章验证并保持blog独立。

Triton-Ascend v3.2.1已从triton-lang官方镜像成功浅克隆，commit2badfc89e70a9b7a5e88463a116c2feddce4b101；原Ascend镜像连接超时，非审批拒绝。可继续补NPU桥接源码篇，与标准Triton3.2.0/NVIDIA链区分。

2026-10-04：第7A三篇与19实验70/70完成（manifest045433-272378），含scope输入5→SCCP结果7、InferType/Reify、AddOne复用与保留旧值的四组CPU数组检查。Triton-Ascend v3.2.1桥接篇与18四仓24阶段检查完成（044720-198954）；无项目构建/设备运行。开始复杂ODS/存储/TypeAttr接口，随后1:N、声明式与工具专题。

第7A站点构建11.60s通过，两个仓库diff --check通过。新增70项最后manifest045433-272378；scope负例由RegionBranch边检查先诊断（空入口数量、i32/i64类型），不是自定义verifyRegions先执行。后续写法需保持这一事实。

第7B两篇complex_ods/storage_interfaces与20工程46/46完成，manifest050220-242921；多组/嵌套与Properties实测、32→40折叠、ArrayRef复制/unique、Type/Attr接口规划、名义递归body冲突。Node为纯C++构造无语法/lowering。工具扩展mlir-reduce/mlir-lsp-server构建88234已输出17/17完成，待poll收尾。下一步21工程1:N与声明式改写。

第7C完成one_to_many/declarative_patterns与21工程43/43，manifest050959-146831，含四组加减CPU结果、缺call规则/非法pair/PDLL语法反例；DRR和PDLL输出一致，canon-only不删my.add。第7B站点12.59s通过。TA桥接图修正阶段箭头后18四仓24阶段重验050620-097861。mlir-reduce/mlir-lsp-server已构建完成，无运行会话。开始第8批，需调试最小复现/测试数值性能方法/C与PythonAPI/bytecode版本插件/quant sparse shape IRDL complex StableHLO定位；第9批还需SCF execute_region/index_switch与已有parallel/forall覆盖连接、全目录审核。

第8A五篇指南与22/23工程完成31/26检查，manifest052510-138042、052749-583326。官方Python绑定已从固定20.1.8构建，Python3.12与依赖见版本矩阵。后续Bytecode/版本/插件、领域定位与有限源码阅读；暂有python_bindings→bytecode链接，待下一篇补齐后站点检查。

2026-10-04 最终交付：第8批及第9批全部完成；当前章节目录与覆盖表约定范围已有正文，新增维护与源码链59项通过。最终站点构建通过，777处正文站内链接、1294处渲染锚点引用无缺失，280处固定LLVM源码路径与跨仓库实验/项目路径核对通过。11—26工程证据及硬件/版本限制集中于[交付报告](./completion_report.md)。用户新增章节阅读状态仍未知；未提交、推送或部署。以下历史记录保留过程语境，最新状态以上表及报告为准。
