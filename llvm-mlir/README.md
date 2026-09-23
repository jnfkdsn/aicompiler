# LLVM / MLIR 实验

本目录服务于“预测 → 运行观察 → 修改 → 解释结果”的学习流程。blog 保存原理与源码解释，实验目录保存可编辑输入、学习步骤和程序；生成的 IR、诊断和日志保存在 workspace 的 `artifacts/`。

| 入口 | 用途 |
|---|---|
| [动手练习](./exercises/README.md) | 自己实现的任务入口；当前提供 clamp 简化的 TODO 骨架、判据与源码阅读路线 |
| `01-ir-basics/sum_positive.mlir` | 已独立编写的基础 IR 程序 |
| `02-pass/twice.mlir` | Pass 与 pipeline 的个人实验输入 |
| [03-ir-api](./03-ir-api/README.md) | 分步观察 RAUW、erase、完整改写、支配错误和克隆映射，可修改输入验证预测 |
| [04-small-pass](./04-small-pass/README.md) | 完整函数 Pass 工程、前后 IR 观察与 lit/FileCheck；阅读后独立扩展左侧加零 |
| [05-op-definition](./05-op-definition/README.md) | 定义 lab.clamp，观察 ODS 生成 API、builder、验证、打印与 Pass 展开 |
| [06-ir-definition](./06-ir-definition/README.md) | 观察通用接口消费、Type/Attr 参数与存储、Region 传值及打印验证 |
| [docs](./docs/README.md) | 文档维护工具及经过编译验证的共享示例代码；`validate_*.py` 的通过计数是回归证据 |

课程配套代码的回归检查不替代学习实验。学习入口应展示输入、关键中间状态、输出与解释线索，并提供有限的修改任务。PatternRewriter 原理示例与小 Pass 工程沿用这个组织方式。

## 现在想动手时

从 [练习 01](./exercises/01-clamp-simplify/README.md) 开始。`03`—`06` 主要是可运行的完整教学示例；`docs/` 主要供维护文档；新增的 `exercises/` 明确保存待你完成的任务。之前这三类入口的区分不够明显，现在分别标明。

第一项只需填写一段匹配/改写逻辑并补用例，构建和注册可以复用。任务中的 [源码阅读路线](./exercises/01-clamp-simplify/SOURCE_READING.md) 从生成验证入口或 replaceOp 的一个具体问题进入上游实现。
