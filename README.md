# AI Compiler Labs

本仓库保存可复现的 AI Compiler 与算子实验。

TVM / PyTorch Compiler 当前课程从 [TVM labs](tvm-e2e/README.md) 和 [PyTorch labs](pytorch-compiler/README.md) 进入，固定环境见 [环境说明](environments/ai-compiler-course.md)。每套都有可观察参考程序和独立练习骨架。

LLVM / MLIR 的学习实验从 [llvm-mlir/README.md](llvm-mlir/README.md) 进入；基础学习后的两个独立任务是 [clamp 简化](llvm-mlir/exercises/01-clamp-simplify/README.md) 和 [按行 Softmax](llvm-mlir/exercises/02-softmax/README.md)。完整示例供按需查阅，练习骨架供实现，文档回归脚本供维护，三类入口分别说明。

跨领域学习顺序见[知识库学习路线](https://github.com/jnfkdsn/blog/blob/main/docs/notes/roadmap.md)，长期能力与项目标准见[编译器能力与项目](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/capabilities.md)。

## 目录

| 目录 | 内容 |
|---|---|
| `llvm-mlir/` | LLVM IR、MLIR、Pass、Dialect Conversion 实验 |
| `tvm-e2e/` | Relax、TensorIR、Schedule、BYOC 与 Runtime 实验 |
| `pytorch-compiler/` | Dynamo、FX、Inductor、AOTInductor 与自定义 backend 实验 |
| `stablehlo/` | StableHLO 语义、转换、版本兼容与 AscendNPU IR 入口实验 |
| `triton-kernels/` | Triton 算子实现、正确性测试和性能实验 |
| `triton-compiler/` | TTIR、Pass Pipeline、lowering 与编译器源码实验 |
| `triton-ascend/` | Triton-Ascend 与 AscendNPU IR 实验 |
| `tilelang/` | TileLang 算子与编译流程实验 |
| `tensorrt/` | TensorRT build、runtime 和 plugin 实验 |
| `ascend-c/` | Ascend C 算子与硬件流水实验 |
| `common/` | 已被多个实验复用的测试、benchmark 和辅助代码 |
| `projects/` | 跨层次综合项目 |
| `environments/` | requirements、Conda、Docker 和版本矩阵 |

大型源码从 `../upstream/` 使用，大型生成物输出到 `../artifacts/`。

每个实验至少说明：目标、环境、运行命令、正确性判据、输出位置和结论。
