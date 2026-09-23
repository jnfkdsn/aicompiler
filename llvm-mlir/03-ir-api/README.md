# C++ IR API 观察实验

先读 blog 的 `compiler/transforms/ir_api.md`，再在这里把“知道 API 的意思”转成“能够预测 IR 会怎样变化”。不要求默写 API；先判断该创建什么、改哪些使用、何时可以删除，再查相应方法。

`twice.mlir` 是供你修改的独立实验输入。观察入口调用 `../docs/ir_api/` 的真实 C++ 程序，展示中间 IR、使用计数、前后差异和诊断；`../docs/validate_*.py` 继续负责文档回归检查。输入不会被脚本改写，每次运行在 workspace 的 `artifacts/logs/mlir-labs/` 下保存独立快照和结果。

环境沿用本地 LLVM/MLIR 20.1.8 构建树、Clang、CMake 与 Ninja。所有命令从 workspace 根目录运行；入口会增量构建示例 C++ 工具，不重建 LLVM。

## 1. 分开观察 RAUW 与 erase

运行前，先预测第一条 `%a = addi %x, %zero` 的变化：

- 原来 `%a` 有几个 use？`%x` 有几个 use？
- 只执行 RAUW 后，旧加法是否还在？`%r` 的哪个输入改变了？
- 再执行 erase 后，为什么 `%x` 的 use 数量也可能改变？

```bash
python3 aicompiler-labs/llvm-mlir/03-ir-api/observe.py
```

输出依次包含 `before`、`after-rauw`、`after-erase` 的实际 IR。对于初始输入，旧结果 use 数为 `1 → 0 → 不再访问已销毁对象`；替代值 `%x` 的 use 数为 `2 → 3 → 2`。RAUW 把 `%r` 的一个输入接到 `%x`，但旧加法仍使用 `%x`；erase 删除旧加法，才移除这条输入边。

打印编号可能变化，比较操作顺序、operand 来源和计数，不要把 `%0` 的重命名误认为值替换。

## 2. 观察完整改写及 use/user

```bash
python3 aicompiler-labs/llvm-mlir/03-ir-api/observe.py --step rewrite
```

逐段对照原始 IR、消除加零后的 IR、创建乘法并清理后的 IR，以及每一步的 diff。回答：为什么简化前后 `%x` 都有两个 use，但不同 user 数从 2 变成 1？为什么零常量只在最后的清理阶段消失？

## 3. 对照合法与非法的插入位置

```bash
python3 aicompiler-labs/llvm-mlir/03-ir-api/observe.py --step dominance
```

先看正常输出，再看故意把常量放到乘法之后的输出和支配诊断。错误案例返回 2 是预期观察；其他错误不会被当成成功。能指出“乘法使用了尚未支配该位置的值”，比记住某个插入 API 名字更重要。

## 4. 对照有无参数映射的克隆

```bash
python3 aicompiler-labs/llvm-mlir/03-ir-api/observe.py --step clone
```

先追踪新函数如何使用自己的参数，再看漏掉映射时哪条引用越过了函数的隔离边界。此处只是单 Block body 的观察，不要求同时学习完整 CFG 克隆。

## 改一处，再验证预测

按需选择一项即可，不作为进入下一章的额外关卡：

1. 把 `%r` 改为 `arith.addi %a, %a`，重新运行第一步。预测 `%a` 的 use 数和不同 user 数，并找出 RAUW 后被转接的两个槽位。
2. 把零常量改成 1，运行 `--step rewrite`。解释为什么规则不再匹配，为什么“成功运行但没有修改”仍然是正常结果。
3. 保留自己的修改，使用 `--input 路径` 比较另一份输入。`dominance` 需要能匹配 `x+x` 的输入，否则不会触发本节故意设置的错误。

第一步专门展示匹配的 `x+0`；没有匹配时会给出诊断，不会假装完成一次 RAUW。这里只运行操作 IR 的编译器程序；正确性依据包括合法性推理与 verifier，尚不包括生成函数的机器码执行或性能测量。
