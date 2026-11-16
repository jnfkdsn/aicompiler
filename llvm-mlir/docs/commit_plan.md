# 当前课程改动的分批 git add 指令

2026-10-04。此文件提供后续暂存方案；编写时没有执行暂存、commit 或 push。两个仓库分别维护历史，父工作区不是 Git 仓库。

## 1. 使用方式

每一批均提供可单独复制的完整命令，使用绝对 `git -C` 路径，所以从任何目录执行都可以。路径以当前 checkout 为准；若换机器，只需替换 `-C` 后的仓库路径。命令中的 `--` 后均为明确文件或实验目录，没有 `git add .` 或全仓库 `git add -A`。

**一次只执行准备处理的一个批次。** `git add` 只暂存，不会替你创建 commit。确认并完成这一批提交后，再执行下一批；若连续执行全部代码块却不逐批提交，所有改动仍会聚在暂存区中。两仓库的 blog/labs 块需要分别检查和提交，不能形成一个跨仓库 commit。

目录参数会递归选择该目录当前未忽略的文件，以及已跟踪文件的修改/删除。下列目录均按实验或独立模块选择；跨主题目录改为枚举文件，避免提前加入后续扩展。共享导航默认在第 15 批收尾，01 批的迁移入口另提供交互式选择。

## 2. 各批次的暂存命令

### L0：`chore(repo): add lab repository scaffold`

根 README 随 01 批加入；环境版本矩阵的完整最终状态随 15 批加入。这里只选择当前已有的占位文件，不递归暂存各项目目录。

blog 当前无对应改动，本批只处理 labs。

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  .gitignore \
  ascend-c/.gitkeep \
  common/.gitkeep \
  environments/conda/.gitkeep \
  environments/docker/.gitkeep \
  environments/requirements/.gitkeep \
  projects/softmax-vertical-trace/.gitkeep \
  pytorch-compiler/.gitkeep \
  stablehlo/.gitkeep \
  tensorrt/.gitkeep \
  tilelang/.gitkeep \
  triton-ascend/.gitkeep \
  triton-compiler/.gitkeep \
  triton-kernels/.gitkeep \
  tvm-e2e/.gitkeep
```

### L1：`docs(cpp): add source and code-generation examples`

blog 当前无对应改动，本批只处理 labs。

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  common/cpp-foundations/
```

### 01：`refactor(mlir): unify my dialect examples and entry`

旧 tutorials/my_dialect 的两条路径已删除但仍在 Git 跟踪中，命令会暂存删除；新导读同时加入。05/06 目录的命令也同时暂存新增 MyOps 和旧 LabOps/Lesson 删除。完成下面的整文件选择后，再按本节的交互命令选择入口迁移。

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/compiler/ir_definition/dialect_basics.md \
  docs/notes/compile/mlir/compiler/ir_definition/op_definition.md \
  docs/notes/compile/mlir/compiler/ir_definition/traits_interfaces.md \
  docs/notes/compile/mlir/compiler/ir_definition/types_attributes.md \
  docs/notes/compile/mlir/compiler/ir_definition/regions_assembly.md \
  docs/notes/compile/mlir/compiler/ir_definition/assembly_format.md \
  docs/notes/compile/mlir/tutorials/my_dialect/01_minimal_dialect.md \
  docs/notes/compile/mlir/tutorials/my_dialect/index.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  README.md \
  llvm-mlir/my-dialect/ \
  llvm-mlir/05-op-definition/ \
  llvm-mlir/06-ir-definition/ \
  llvm-mlir/exercises/01-clamp-simplify/ \
  llvm-mlir/docs/validate_my_dialect.py \
  llvm-mlir/docs/validate_op_definition.py \
  llvm-mlir/docs/validate_ir_definition.py
```

入口迁移涉及共享文件，再执行下面的交互命令。只选择旧 `tutorials/my_dialect` 引用改到 `compiler/ir_definition/dialect_basics`、基础五篇命名及相关入口说明；新增 Conversion、高级接口和其他后续模块的段落留给后续批次。按 `y` 暂存当前块，`n` 跳过，`s` 尝试拆块；同一块混合多个主题且无法拆开时，用 `e` 编辑补丁或先跳过，不要直接全部选入。

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -p -- \
  docs/notes/compile/mlir/compiler/ir_definition/index.md \
  docs/notes/compile/mlir/tutorials/index.md \
  docs/notes/compile/mlir/index.md \
  docs/notes/compile/mlir/learning_path.md \
  docs/notes/compile/mlir/coverage.md
```

### 02：`feat(mlir): add dialect and type conversion lessons`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/compiler/conversion/operation_conversion.md \
  docs/notes/compile/mlir/compiler/conversion/type_conversion.md \
  docs/notes/compile/mlir/compiler/conversion/materialization.md \
  docs/notes/compile/mlir/compiler/conversion/boundaries.md \
  docs/notes/compile/mlir/compiler/conversion/advanced.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/07-dialect-conversion/ \
  llvm-mlir/08-type-conversion/ \
  llvm-mlir/docs/validate_conversion.py \
  llvm-mlir/docs/validate_type_conversion.py
```

### 03：`feat(mlir): add tensor and linalg learning path`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/dialects/tensor/ \
  docs/notes/compile/mlir/dialects/linalg/ \
  docs/notes/compile/mlir/tutorials/pipelines/overview.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/09-tensor-linalg/ \
  llvm-mlir/docs/validate_tensor_linalg.py
```

### 04：`feat(mlir): connect buffers to CPU execution`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/dialects/memref/ \
  docs/notes/compile/mlir/dialects/llvm/ \
  docs/notes/compile/mlir/compiler/memory/bufferization.md \
  docs/notes/compile/mlir/compiler/memory/one_shot.md \
  docs/notes/compile/mlir/compiler/memory/ownership.md \
  docs/notes/compile/mlir/compiler/lowering/ \
  docs/notes/compile/mlir/tutorials/pipelines/cpu.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/10-memory-bufferization/ \
  llvm-mlir/11-cpu-lowering/ \
  llvm-mlir/docs/validate_memory.py \
  llvm-mlir/docs/validate_cpu.py
```

### 05：`feat(mlir): explain analysis and optimization legality`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/compiler/analysis/dominance_liveness.md \
  docs/notes/compile/mlir/compiler/analysis/alias_effects.md \
  docs/notes/compile/mlir/compiler/analysis/caching.md \
  docs/notes/compile/mlir/compiler/analysis/dataflow.md \
  docs/notes/compile/mlir/compiler/analysis/legality.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/12-analysis/ \
  llvm-mlir/docs/validate_analysis.py
```

### 06：`feat(mlir): add math and softmax walkthroughs`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/dialects/math/scalar_math.md \
  docs/notes/compile/mlir/dialects/math/index_arithmetic.md \
  docs/notes/compile/mlir/tutorials/kernels/reduction_softmax.md \
  docs/notes/compile/mlir/tutorials/kernels/softmax_storage.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/13-softmax/ \
  llvm-mlir/docs/validate_softmax.py
```

### 07：`feat(mlir): add structured optimization and vector schedules`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/dialects/affine/ \
  docs/notes/compile/mlir/dialects/vector/ \
  docs/notes/compile/mlir/compiler/optimization/
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/14-structured-optimization/ \
  llvm-mlir/15-vector-transform/ \
  llvm-mlir/docs/validate_structured.py \
  llvm-mlir/docs/validate_vector.py
```

### 08：`feat(mlir): add matmul and attention case studies`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/tutorials/kernels/matmul.md \
  docs/notes/compile/mlir/tutorials/kernels/attention.md \
  docs/notes/compile/mlir/tutorials/kernels/online_attention.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/17-matmul-attention/ \
  llvm-mlir/docs/validate_attention.py
```

### 09：`feat(mlir): add GPU and NPU compilation paths`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/dialects/gpu/ \
  docs/notes/compile/mlir/compiler/targets/
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/16-gpu-execution/ \
  llvm-mlir/docs/validate_gpu.py
```

### 10：`docs(compilers): trace pinned frontend and backend sources`

source_map.json 随实验目录加入固定源码版本。环境矩阵中的项目汇总在 15 批加入。

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/tutorials/pipelines/frontend.md \
  docs/notes/compile/triton/compiler_path.md \
  docs/notes/compile/triton/ascend_compiler_path.md \
  docs/notes/compile/triton/index.md \
  docs/notes/compile/npu-ir/source_path.md \
  docs/notes/compile/npu-ir/index.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/18-project-paths/
```

### 11：`feat(mlir): add advanced definitions and conversions`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/compiler/ir_definition/type_shape_inference.md \
  docs/notes/compile/mlir/compiler/ir_definition/region_interfaces.md \
  docs/notes/compile/mlir/compiler/ir_definition/complex_ods.md \
  docs/notes/compile/mlir/compiler/ir_definition/storage_interfaces.md \
  docs/notes/compile/mlir/compiler/memory/custom_operations.md \
  docs/notes/compile/mlir/compiler/conversion/one_to_many.md \
  docs/notes/compile/mlir/compiler/transforms/declarative_patterns.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/19-extension-interfaces/ \
  llvm-mlir/20-ods-storage/ \
  llvm-mlir/21-conversion-patterns/ \
  llvm-mlir/docs/validate_interfaces.py \
  llvm-mlir/docs/validate_ods_storage.py \
  llvm-mlir/docs/validate_conversion_patterns.py
```

### 12：`feat(mlir): add debugging bindings and extension tools`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/guides/debugging.md \
  docs/notes/compile/mlir/guides/regression_tests.md \
  docs/notes/compile/mlir/guides/numerics_performance.md \
  docs/notes/compile/mlir/guides/c_api.md \
  docs/notes/compile/mlir/guides/python_bindings.md \
  docs/notes/compile/mlir/guides/bytecode.md \
  docs/notes/compile/mlir/guides/plugins.md \
  docs/notes/compile/mlir/tutorials/first_pass.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/22-debug-testing/ \
  llvm-mlir/23-bindings/ \
  llvm-mlir/24-bytecode-plugins/ \
  llvm-mlir/docs/validate_debugging.py \
  llvm-mlir/docs/validate_bindings.py \
  llvm-mlir/docs/validate_bytecode_plugins.py
```

### 13：`docs(mlir): introduce domain-specific representations`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/dialects/extensions/ \
  docs/notes/compile/mlir/dialects/math/complex.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/25-domain-extensions/ \
  llvm-mlir/docs/validate_domains.py
```

### 14：`feat(mlir): connect regions IR maintenance and source reading`

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/dialects/scf/regions_switch.md \
  docs/notes/compile/mlir/dialects/scf/parallel_results.md \
  docs/notes/compile/mlir/compiler/transforms/ir_maintenance.md \
  docs/notes/compile/mlir/compiler/analysis/resources_effects.md \
  docs/notes/compile/mlir/guides/source_reading.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  llvm-mlir/26-ir-maintenance/ \
  llvm-mlir/docs/validate_maintenance.py
```

### 15：`docs(mlir): consolidate reading order coverage and delivery`

在先前批次完成后执行。本批将共享导航的剩余改动、完整阅读路线、环境与交付汇总一起暂存；01 批已经提交的迁移段落不会重复产生 diff。

blog：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog add -- \
  docs/notes/compile/mlir/chapter_plan.md \
  docs/notes/compile/mlir/learning_path.md \
  docs/notes/compile/mlir/coverage.md \
  docs/notes/compile/mlir/index.md \
  docs/notes/compile/mlir/compiler/index.md \
  docs/notes/compile/mlir/compiler/ir_definition/index.md \
  docs/notes/compile/mlir/compiler/transforms/index.md \
  docs/notes/compile/mlir/compiler/conversion/index.md \
  docs/notes/compile/mlir/compiler/memory/index.md \
  docs/notes/compile/mlir/compiler/analysis/index.md \
  docs/notes/compile/mlir/dialects/index.md \
  docs/notes/compile/mlir/dialects/scf/index.md \
  docs/notes/compile/mlir/dialects/math/index.md \
  docs/notes/compile/mlir/guides/index.md \
  docs/notes/compile/mlir/tutorials/index.md \
  docs/notes/compile/mlir/tutorials/kernels/index.md \
  docs/notes/compile/mlir/tutorials/pipelines/index.md
```

labs：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -- \
  environments/version-matrix.md \
  llvm-mlir/README.md \
  llvm-mlir/docs/README.md \
  llvm-mlir/docs/chapter_review.md \
  llvm-mlir/docs/completion_goal.md \
  llvm-mlir/docs/completion_report.md \
  llvm-mlir/docs/commit_plan.md
```

## 3. 中间版本和共享文件

这些命令完成的是现有最终文件的主题分组，不会自动重写正文中的向后引用。Conversion 的 advanced 已链接后续的 1:N，其他正文也可能链接尚未加入的章节。因此，不能仅凭执行本清单就声称每一个中间 commit 都能独立构建网站。

默认方案将跨主题的完整首页、学习路线和环境汇总留到 15 批，最终版本集中验证。如果要求每一个中间提交也能构建，需要另外制作分阶段补丁：未来链接先作为普通文字，目标文章加入后再恢复链接；这项拆分不应通过新增空白迁移页实现。01 批的迁移链接则与删除旧页同时处理，避免丢失原有入口。

需要将共享文件的一部分提前随主题提交时，使用交互式暂存。对于尚未跟踪的新文件，先用 `-N` 标记 intent-to-add，`-p` 才能选择新增内容。例如只提前保存基础 LLVM 配置：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -N -- \
  environments/version-matrix.md
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs add -p -- \
  environments/version-matrix.md
```

上述是可选的分段操作，`-N` 本身也会修改索引。只选择当前批次对应的内容，未来的 NVPTX、Python 和项目快照状态暂不选入。15 批的整文件命令最终收齐余下内容。不要在分段之后紧接着运行同一文件的普通 `git add`，否则会把未选段落也全部暂存。

04 可继续拆为内存/CPU，07 可拆为结构化变换/Vector，11 和 12 可按所含实验再次拆分。需要这些更细粒度提交时，从对应块中选择完整实验及对应验证脚本，不把源码与测试分离。

## 4. 每批检查与复现边界

执行所选批次的 add 命令后，可分别检查两个暂存区：

```bash
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog diff --cached --stat
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog diff --cached --check
git -C /home/jnfkdsn/workspace/aicompiler-workspace/blog diff --cached
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs diff --cached --stat
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs diff --cached --check
git -C /home/jnfkdsn/workspace/aicompiler-workspace/aicompiler-labs diff --cached
```

确认只包含当前主题后，再自行提交。本文件不包含自动 commit、push、reset 或清空暂存区命令。已有暂存内容不会被这些 add 命令自动隔离，因此开始一批前应先查看当前暂存区。

部分 labs 验证脚本会读取兄弟 blog 仓库正文，验证时需要两仓检出对应主题。源码、输入、观察脚本、README 和 `validate_*.py` 保持同批。网站发布前检查全部站内链接与完整构建；先使 labs 文件在 GitHub 可访问，再发布引用它们的 blog。

`artifacts/` 的构建、venv、目标文件和原始日志，以及 `upstream/` 源码不在这些命令范围内。`common/cpp-foundations/generated/` 是教学例子，冻结的 benchmark 记录也属于复现材料，按对应主题保留。

父目录的 `WORKSPACE.md`、`writing_method.md` 不属于这两个 Git 仓库，以上命令不会保存它们。L0/L1 是此前积累的独立内容，不默认归入最近一批 MLIR 新课。
