# 环境版本矩阵
llvm-project commit 87f0227cb60147a26a1eeb4fb06e3b505e9c7261

## TVM / PyTorch Compiler 课程（2026-10-17）

- 隔离环境 `artifacts/venvs/ai-compiler-course`：Python3.12.4、PyTorch2.7.1+cpu、NumPy1.26.4；完整锁定清单见 [requirements](ai-compiler-course-requirements.txt)。
- TVM v0.20.0 `1c60502cfba5ca4ed948e07bf6c064426418187d`，LLVM14.0.0，CPU工具链与Cython3.0.12绑定已构建，未改变MLIR20环境。
- 两套各7组CPU观察已执行，含动态形状、调度/融合、产物加载、AOT及梯度；具体证据和限制见 [交付报告](compiler-courses-report.md)。
- GPU重新检查仍返回系统禁止访问，未发现可用NPU设备；不将设备机制说明记录为已验证设备执行。两套课程的CPU记录不改变下方Ascend planned组合。


这里只记录会影响实验复现的核心组合。某次实验的精确源码版本由 artifact manifest 中的 commit hash 补充。

| 环境名 | Triton-Ascend | CANN | PyTorch | torch_npu | Python | 设备 | 状态 |
|---|---:|---:|---:|---:|---:|---|---|
| `ascend-a2-3.2.1` | 3.2.1 | 9.0.0 | 2.7.1 | 2.7.1.post4 | 待填写 | Atlas A2 | planned |

状态建议使用：

- `planned`：计划使用，尚未验证。
- `working`：基本运行通过。
- `verified`：关键实验已完成正确性和性能验证。


## MLIR 教程工具链（2026-10-04）

- LLVM/MLIR：llvmorg-20.1.8，commit `87f0227cb60147a26a1eeb4fb06e3b505e9c7261`；构建在 `artifacts/builds/mlir-20.1.8`，RTTI 关闭。
- 已将 `LLVM_TARGETS_TO_BUILD` 扩展为 `Native;NVPTX` 并完成 mlir-opt、mlir-translate、llc 重建。
- NVIDIA 编译验证：CUDA ptxas 12.4.131，目标 sm_80/+ptx70；PTX→cubin 和 Host object 编译通过，当前系统阻止 GPU 访问，未链接/执行设备程序或测量性能。
- CPU 数值与固定 x86-64 小规模计时见各实验 manifest。新增后端不把上方 planned 的 Ascend 软件/硬件组合改成 verified。

项目源码快照：torch-mlir `528d3dcb9a2288743b62df9f4937b1689787e38a`、Triton v3.2.0 `9641643da6c52000c807b5eeed05edaec4402a67`、AscendNPU-IR `37c6ebc33d1789500014e6a7b2b62164b3cb566b`。只做源码阅读，各项目自己的 LLVM 依赖记录在 `llvm-mlir/18-project-paths/source_map.json`；未构建这些项目。

## MLIR 工具与绑定补充（2026-10-04）

- 同一LLVM构建 assertions ON；外部C++工程按此配置处理NDEBUG，尤其含Statistic字段时。
- 已构建 mlir-reduce、mlir-lsp-server；22工程完成重放/缩减和LSP协议握手，未配置完整IDE或GDB会话。
- MLIR_ENABLE_BINDINGS_PYTHON=ON，官方 MLIRPythonModules 已构建。Python 3.12 venv：artifacts/venvs/mlir-python20；包路径：artifacts/builds/mlir-20.1.8/tools/mlir/python_packages/mlir_core。
- Python依赖：nanobind2.4.0、pybind11 2.13.6、numpy2.1.2、PyYAML6.0.1、ml_dtypes0.5.3，固定清单见 llvm-mlir/23-bindings/python-requirements.txt。
- C API静态库 MLIRCAPIIR/Arith/Func/Transforms 已构建；23工程C与Python产生相同42→7的IR，包含生命周期和失败阶段检查。
- Triton-Ascend v3.2.1源码快照2badfc89e70a9b7a5e88463a116c2feddce4b101；专属LLVM与AscendNPU-IR子模块版本见18工程，不等同独立NPU仓库快照。
