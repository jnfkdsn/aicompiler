# AI Compiler Labs

本仓库保存可复现的 AI Compiler 与算子实验。

LLVM / MLIR 的学习实验从 [llvm-mlir/README.md](llvm-mlir/README.md) 进入；当前主线从 [my.add 增量工程](llvm-mlir/my-dialect/README.md) 进入，其他任务保留在 [MLIR exercises](llvm-mlir/exercises/README.md)。完整示例供观察，练习骨架供实现，文档回归脚本供维护，三类入口分别说明。

整个 workspace 的学习顺序和阶段完成标准见 [`stack_and_roadmap.md`](https://github.com/jnfkdsn/blog/blob/main/docs/notes/compile/ai-compiler/stack_and_roadmap.md)。

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
