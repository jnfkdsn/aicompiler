# 定义 IR 抽象：接口、类型/属性与 Region

这组观察配套 blog 的 `compiler/ir_definition/traits_interfaces.md`、`types_attributes.md`、`regions_assembly.md`、`assembly_format.md`。先沿正文理解机制，再选择一个小变化预测并观察；不要求先运行工程才能读懂正文。

工程复用 `../05-op-definition/` 的 Lab dialect，新增 `lesson` dialect。两个方言在同一工具中共存；前一个实验的源码不需要修改。

## 按章观察

从 workspace 根目录运行，首次会使用现有 LLVM/MLIR 20.1.8 库生成 TableGen 代码并构建：

```bash
python3 aicompiler-labs/llvm-mlir/06-ir-definition/observe.py --section interfaces
python3 aicompiler-labs/llvm-mlir/06-ir-definition/observe.py --section types
python3 aicompiler-labs/llvm-mlir/06-ir-definition/observe.py --section regions
python3 aicompiler-labs/llvm-mlir/06-ir-definition/observe.py --section assembly
```

省略 `--section` 会展示全部。脚本打印具体 IR、接口报告、DCE 结果和 checked 构造诊断；日志放在 `artifacts/logs/mlir-ir-definition/<时间>/`。生成源码与二进制放在 `artifacts/builds/mlir-ir-definition/`。构建仍使用工作区既有 clang/clang++、Ninja 和 MLIR CMake 配置，不重新构建 LLVM。

| 输入/工具 | 先预测 | 应观察到 |
|---|---|---|
| `interfaces.mlir` | 两个结果无人使用，通用工具有足够事实删除谁？ | lab.clamp 被删除；缺少效果信息的 opaque_clamp 保留 |
| `direct.mlir` | 不引入自定义类型，操作怎样直接回答查询？ | lesson.clamp 的成员方法返回 [-4,7]；不注册外部模型也可查询 |
| `lesson-opt` / `lesson-opt-no-model` | 移除外部范围模型会同时改变 DCE 吗？ | clamp 的 bounds 变 unknown；原有 Pure 信息及 dead 判断不变 |
| `types.mlir` | 属性与结果类型保存相同区间，会不会成为同一对象？ | 通用格式显示两类字段；直接范围接口可以回答 [-4,7] |
| `type-probe` | 两次请求相同参数，会得到相等的类型吗？ | same_parameters=1；不同参数比较为 0；非法 checked 请求诊断后返回空句柄 |
| `scope.mlir` | 哪些值进入，哪些值退出？ | 单值 clamp、多结果 swap、空参数/结果三个结构均合法 |
| `assembly.mlir` | 通用打印会丢失 same 语法或 tag 吗？ | 通用格式不写 same；再次正常打印恢复关键字，tag 和引用关系保留 |

`types.mlir` 刻意书写完整的 `#lesson.bounds` 和 `!lesson.range`。由于 ODS 已知道 limit 的具体属性/结果类型种类，正常打印可将操作中的字段缩写成 `bounds(<-4, 7>) : <-4, 7>`；函数签名等通用类型位置仍带前缀。它们表示同一对象，不是另一种计算。

## 单独运行工具

先通过观察脚本完成构建，也可以手工运行：

```bash
cmake -S aicompiler-labs/llvm-mlir/06-ir-definition \
  -B artifacts/builds/mlir-ir-definition -G Ninja \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DLLVM_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/llvm" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++ \
  -DCMAKE_C_COMPILER=/usr/bin/clang
cmake --build artifacts/builds/mlir-ir-definition -j2

artifacts/builds/mlir-ir-definition/lesson-opt \
  aicompiler-labs/llvm-mlir/06-ir-definition/interfaces.mlir \
  --pass-pipeline='builtin.module(func.func(lesson-report))'

artifacts/builds/mlir-ir-definition/lesson-opt \
  aicompiler-labs/llvm-mlir/06-ir-definition/interfaces.mlir \
  --canonicalize --verify-each

artifacts/builds/mlir-ir-definition/lesson-opt \
  aicompiler-labs/llvm-mlir/06-ir-definition/scope.mlir \
  --mlir-print-op-generic
```

`lesson-report` 输出到 stderr，IR 输出到 stdout。`type-probe` 最后一项故意请求非法区间，诊断是预期现象，程序处理失败后仍返回成功。

## 源码怎样找

| 文件 | 主要责任 |
|---|---|
| `Lesson.td` | 接口、Type/Attr、操作及结构/效果声明 |
| `Lesson.h` / `Lesson.cpp` | 生成代码接入、dialect 注册、参数和区域验证、手写格式 |
| `lesson-opt.cpp` | 报告 Pass、外部模型与 Context 注册；构建两个对照工具 |
| `type-probe.cpp` | 类型 uniquing 与 checked 构造 |
| `tests/invalid.mlir` | 15 个预期失败模块：参数、跨字段、区域、隔离与语法 |

范围接口只承诺静态结果边界，工具只报告它，没有实现范围分析或比较折叠。`lesson.limit` 和 `lesson.scope` 尚未提供 lowering，不可据打印结果声称已执行数值计算。`lesson.scope` 目前没有 RegionBranchOpInterface，多组 variadic 分段也只在正文解释，未在工程中实现。

## 阅读后再选一个变化

1. 将 `interfaces.mlir` 中的 clamp 结果返回，先预测 bounds 与 dead 各自怎样变化。
2. 将 `types.mlir` 中属性和结果同时改成 `[7,7]`；再只改其中一处，定位不同验证层。
3. 在 scope 的 swap 中仅交换 yield 顺序，观察出口类型对应错误。再将 body 的 `%local` 换成 `%x`，观察隔离约束。
4. 在 `assembly.mlir` 增加一个额外属性，观察通用打印往返是否保留它。

这些是有限的巩固方向，个人实践完成状态在实际提交并解释改动后记录。不要把运行维护脚本等同于完成实验。

## 回归维护

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_ir_definition.py

artifacts/builds/mlir-ir-definition/lesson-opt \
  aicompiler-labs/llvm-mlir/06-ir-definition/tests/invalid.mlir \
  --split-input-file --verify-diagnostics -o /dev/null
```

维护脚本构建并运行观察程序，提取四篇正文中 `irdef-example` / `irdef-invalid` 的完整模块，检查源码片段一致性、格式往返、接口注册对照、实际 DCE、use 引用、类型身份、边界和预期诊断。manifest、命令及输出进入 `artifacts/logs/mlir-docs/<日期>-ir-definition/`。

固定版本：`llvmorg-20.1.8`，commit `87f0227cb60147a26a1eeb4fb06e3b505e9c7261`。验证针对编译器侧结构与行为，不包含目标机器码执行、性能测量或全部 MLIR 测试。
