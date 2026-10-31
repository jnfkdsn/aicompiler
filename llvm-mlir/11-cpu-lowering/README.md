# CPU Lowering、C ABI 与 JIT

对应 blog 的 LLVM 三篇、CPU lowering 三篇与 `tutorials/pipelines/cpu.md`。主线是同一个矩阵加法如何从 Linalg 变成可被 C 调用的函数，另用小标量例子观察 LLVM translation 和 JIT。

命令从 workspace 根目录执行。固定 LLVM `llvmorg-20.1.8`；当前 C 驱动只支持本系列验证的 64 位 host ABI，不作为跨目标通用描述符定义。

## 工具准备

```bash
cmake --build artifacts/builds/mlir-20.1.8 \
  --target mlir-opt mlir-translate llc mlir-runner mlir_c_runner_utils \
  --parallel 2
```

`mlir-runner` 用于 JIT。系统 clang 负责 C 编译和目标文件链接；LLVM IR 始终交给同版本 llc，避免旧 clang 解析新 IR 的兼容问题。生成物保存在 artifacts。

## 从 Linalg 到循环和 CF

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/11-cpu-lowering/add-into.mlir \
  --convert-linalg-to-loops --lower-affine --verify-each

artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/11-cpu-lowering/sum.mlir \
  --convert-scf-to-cf --verify-each
```

第一条命令应显示两个 dim、两重循环、两次 load、一次 addf 与一次 store；输出旧元素没有被读取。第二条把迭代索引和累加值传给 header，再从回边传入更新值。先手推 `[3,-2,5,7]` 的各轮状态，再看是否对应。

## 描述符、C Wrapper 与最小 AOT 程序

以下逐条命令可以独立运行，不需要观察脚本：

```bash
mkdir -p artifacts/builds/mlir-cpu-docs
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/11-cpu-lowering/add-into.mlir \
  --convert-linalg-to-loops --lower-affine --convert-scf-to-cf \
  --convert-to-llvm --reconcile-unrealized-casts --verify-each \
  -o artifacts/builds/mlir-cpu-docs/add-llvm.mlir
artifacts/builds/mlir-20.1.8/bin/mlir-translate --mlir-to-llvmir \
  artifacts/builds/mlir-cpu-docs/add-llvm.mlir \
  -o artifacts/builds/mlir-cpu-docs/add.ll
artifacts/builds/mlir-20.1.8/bin/llc -filetype=obj -relocation-model=pic -O0 \
  artifacts/builds/mlir-cpu-docs/add.ll \
  -o artifacts/builds/mlir-cpu-docs/add.o
clang -std=c11 aicompiler-labs/llvm-mlir/11-cpu-lowering/minimal_driver.c \
  artifacts/builds/mlir-cpu-docs/add.o \
  -o artifacts/builds/mlir-cpu-docs/run
artifacts/builds/mlir-cpu-docs/run
```

预期六行输出：11、22、33、44、55、66。`minimal_driver.c` 与 blog 正文一致，错误结果产生非零退出码。

`read2d.mlir` 用于查看一个二维 MemRef 怎样展开为字段参数，再由 `_mlir_ciface_read2d` 接收结构体指针。`make-copy.mlir` 显示返回结构体的 C wrapper 如何增加第一个结果指针参数。对应 C 原型见 `driver.c`。

## Translation 与 JIT

```bash
artifacts/builds/mlir-20.1.8/bin/mlir-translate \
  aicompiler-labs/llvm-mlir/11-cpu-lowering/choose.mlir --mlir-to-llvmir

artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/11-cpu-lowering/jit.mlir \
  --convert-to-llvm --reconcile-unrealized-casts \
  -o artifacts/builds/mlir-cpu-docs/jit.mlir
artifacts/builds/mlir-20.1.8/bin/mlir-runner \
  artifacts/builds/mlir-cpu-docs/jit.mlir -e main -entry-point-result=i32
```

第一条展示 join Block 的参数如何成为 PHI。JIT 工具应打印返回值 42，工具自身成功退出；不是让进程以状态码 42 退出。本例会常量折叠，只验证执行通路。

## 观察入口

```bash
python3 aicompiler-labs/llvm-mlir/11-cpu-lowering/observe.py --stage loops
python3 aicompiler-labs/llvm-mlir/11-cpu-lowering/observe.py --example read2d --stage llvm
python3 aicompiler-labs/llvm-mlir/11-cpu-lowering/observe.py --example pointer --stage asm
python3 aicompiler-labs/llvm-mlir/11-cpu-lowering/observe.py --native --jit
```

入口打印输入、命令和所选中间结果。`--native` 构建并运行扩展 C 驱动，逐项打印 33 个 actual/expected，包括连续/非连续矩阵、空域、窗口外写入检查、不同访问基址、循环归约、分支和返回新数组。`--jit` 额外执行最小入口。

完整 native 工程链接 `mlir_c_runner_utils` 以提供所需支持函数；最小 add 程序不需要它。所有命令及 IR、LLVM IR、对象文件与程序保存在本次日志目录。

## 两个有限修改任务

1. **新形状。** 在工作副本中为 C 驱动增加一个 `3×2`、带非零 offset 的矩阵用例，先算每个逻辑元素的存储位置。编译同一份 MLIR，检查数值及窗口外不被改写。不要改参考输入的计算语义。
2. **结果与所有权。** 阅读 `make-copy.mlir` 的 C wrapper，解释第一个参数为什么是输出指针、返回描述符和数据分配各归谁。增加读取一个返回元素的观察，再删除最后的 free，说明数值检查为什么仍可能通过却不再形成完整生命周期；实际提交版本恢复匹配的释放。

不要通过错误指针、错误静态 stride 或重复释放来“试一下是否崩溃”。这些不一定被 verifier 检测，未崩溃也不能证明契约成立；需要失败案例时优先采用编译器能明确拒绝的类型或接口错误。

## 作者验证

```bash
python3 aicompiler-labs/llvm-mlir/docs/validate_cpu.py
```

覆盖 8 个完整输入、正文实际输出、C 代码对应、32/64 位 index 转换、33 个扩展 C 数值观察、正文的 6 个结果与 JIT 42；区分非法浮点操作、翻译器注册/接口缺失和链接符号缺失。仅作本机正确性与接口证据，不测性能；32 位 index 仅验证转换，不宣称完成 32 位目标执行。
