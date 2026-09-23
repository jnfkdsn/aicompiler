# PatternRewriter 原理复现

主文档：`blog/docs/notes/compile/mlir/compiler/transforms/rewriting.md`；进阶篇：同目录 `rewrite_drivers.md`。这里保存正文的编译器侧 C++ 示例与 CMake 工程，尚未封装为正式 Pass。输入与输出属于同一模块的 IR，示例不执行生成函数的机器码。

先读正文中的规则、状态表和输出。维护检查从 workspace 根目录运行：

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_rewriting.py
```

使用现有 LLVM/MLIR 20.1.8 构建树、Clang 与 Ninja 增量构建本示例。源码片段对应、输出、轨迹、匹配反例与收敛边界均保存到 `artifacts/logs/mlir-docs/<日期>-rewriting/`。通过计数用于回归检查。

需要观察具体行为时，直接使用已构建的工具。以下命令复用可编辑的 IR API 实验输入，不会修改输入文件：

```bash
artifacts/builds/mlir-rewriting-docs/rewriting-demo greedy aicompiler-labs/llvm-mlir/03-ir-api/twice.mlir
artifacts/builds/mlir-rewriting-docs/rewriting-demo walk aicompiler-labs/llvm-mlir/03-ir-api/twice.mlir
artifacts/builds/mlir-rewriting-docs/rewriting-demo fold-only aicompiler-labs/llvm-mlir/03-ir-api/twice.mlir
```

stdout 是实际输出 IR；stderr 是成功规则轨迹和 Greedy 的 `converged` / `changed`，Walk 则只报告完成单次遍历。比较乘法是否继续成为移位、零常量是否清理，以及有无 `APPLY` 记录。若已经修改过实验输入，输出可能与正文不同，先核对匹配前提。

| 模式 | 规则与驱动 |
|---|---|
| greedy / walk | 相同 A/B/C 规则，用两种 driver 对照 |
| empty / fold-only | 空 Pattern 集合，分别关闭或开启 folding；均关闭常量 CSE 与 Region 简化 |
| single | 主章的单条加零规则，Walk 驱动；用验证生成的 `rewriting-single-input.mlir`，输出保留死常量 |
| in-place | 先把左侧零交换到右侧，再尝试加零消除；用正文 `rewriting-left-zero` 输入 |
| prefer-mul / prefer-shift | 对 `x+x` 的两个候选调整 benefit；用正文 `rewriting-double-input` |
| cycle | 加倍加法与乘法往返，有限预算内停止，返回 2；用正文 `rewriting-double-input` |

正文输入经维护脚本提取后，以对应名称保存在当日日志目录。`cycle` 的返回 2 表示这里预期的 driver 未收敛，不是 parser/verifier 失败；工具也会验证停止后的 IR。其他错误不能当作这项观察通过。

本次先提供完整原理与可观察证据。独立编写、注册并测试小 Pass 的实验将在下一步安排，不以读完这个复现程序代替独立实现。
