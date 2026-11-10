# 固定版本的项目源码阅读

本目录帮助沿有限路径定位真实信息的产生与消费。它不编译这些项目，不安装依赖，也不把字符串检查当成项目行为测试。

| 项目 | 连续任务 | 对应正文 |
|---|---|---|
| torch-mlir | Export/FX → Torch mm → 规则 → 后端类型边界 → 测试 | `mlir/tutorials/pipelines/frontend` |
| Triton v3.2.0 | 程序逻辑块 → load 定义 → encoding → coalesce → NVIDIA lowering | `triton/compiler_path` |
| AscendNPU-IR | VAdd 定义 → 生成配置 → 库接口 → 转换 → 测试 → Host 启动 | `ai-compiler/npu-ir/source_path` |

源码已位于 workspace `upstream/`。精确提交和 LLVM 依赖写入 `source_map.json`，三者都不默认兼容标准 MLIR 20.1.8 构建。

```bash
python3 aicompiler-labs/llvm-mlir/18-project-paths/observe.py --project torch
python3 aicompiler-labs/llvm-mlir/18-project-paths/observe.py --project triton
python3 aicompiler-labs/llvm-mlir/18-project-paths/observe.py --project npu
```

输出每个阶段的路径、实际行号与附近片段。先根据正文说明每步输入/输出，再展开需要的函数体；不以读完目录下全部文件为目标。若 anchor 或 commit 改变，脚本明确报告差异，不静默声称同一版本。

可完成的阅读任务：

1. torch：解释单独运行 TorchToLinalg 为什么仍可能出现 `torch_c` 桥接；在 pipeline 里定位闭合函数类型的步骤。
2. Triton：解释 ptr、mask、other 的 encoding 为什么需要保持对应；找到 mask alignment 限制读取向量宽度的消费位置。
3. NPU：从 VAdd 的最大库 rank=3 推导四维输入还需什么改写；核对上游测试，不把 f16 的库函数名套给 i16。

维护记录：

```bash
python3 aicompiler-labs/llvm-mlir/18-project-paths/observe.py --project all --check
```

manifest 保存固定提交、LLVM gitlink/hash、源文件和正文哈希以及入口行号。当前证据是源码检查；Python 环境未装 torch/torch_mlir/triton，Ascend 子模块与 CANN 也未构建。标准 Linalg/CPU 算法的数值证据在 17 实验，两者分开记录。

Triton-Ascend v3.2.1 使用 `--project ascend`；审计同时核对 LLVM hash 与 AscendNPU-IR gitlink，未初始化/构建子模块。当前四仓库共 24 个阶段。
