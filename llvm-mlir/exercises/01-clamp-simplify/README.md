# 练习 01：将固定区间的 clamp 简化为常量

这是你来实现的练习。已提供可构建的工具、Pass 注册和行为检查；`Exercise.cpp` 中的匹配与改写逻辑留空。前置是已经学过的 Pass、PatternRewriter 和操作定义，无需先完成自定义 Type/Attr、Region 或 Dialect Conversion。

## 要实现的行为

`lab.clamp` 将一个有符号 i32 输入限制在闭区间 `[lower, upper]`。当两端相等时，输出应与输入无关。实现名为 `student-simplify-clamp` 的 Pass 中那一条规则，使下面的输入：

```text
func.func @clip(%x: i32) -> i32 {
  %r = lab.clamp %x bounds(-4, -4) : i32
  return %r : i32
}
```

得到这样的结果（SSA 名称可以不同）：

```text
func.func @clip(%x: i32) -> i32 {
  %c = arith.constant -4 : i32
  return %c : i32
}
```

契约：

- 两端相等的合法 clamp 替换成相应 i32 常量，处理正数、零和负数。
- 两端不相等时保留 clamp，未匹配路径不得修改 IR。
- 原结果的所有 use 都要更新，输出通过 verifier。
- 非法的下界大于上界由已有 verifier 拒绝，不能靠这条规则“修好”。

工具只运行这一项练习 Pass，不混入 canonicalize 或已有的 clamp 展开 Pass，便于确认结果来自你写的规则。

## 从哪里开始

在 workspace 根目录运行：

```bash
python3 aicompiler-labs/llvm-mlir/exercises/01-clamp-simplify/check.py --stage starter
```

你会看到规范化的输入和 Pass 输出。初始骨架的两者相同：TODO 返回匹配失败，尚未实现简化。最后的 starter 成功只表示工程可运行、IR 验证及非法输入诊断正常。

本轮主要编辑：

| 文件 | 你的工作 |
|---|---|
| `Exercise.cpp` | 完成 `SimplifyClamp::matchAndRewrite` 中的 TODO |
| `input.mlir` | 读已有正反例，再补一个你自己选择的边界用例及 CHECK |
| 自建 `NOTES.md` | 简短写出合法性理由、边界选择、结果与预测不符的经历 |

CMake、`student-opt.cpp` 和 Pass 外壳已配好，第一轮可先复用。这个工程链接 `05-op-definition` 的 LabOps 库，源定义保持在原处；修改练习时无需改参考工程、生成文件或上游源码。

## 先作决定，再写代码

先用自己的话说明：为什么两端相等时，任意合法 i32 输入都会得到同一个值？再看 `input.mlir`：哪几条 clamp 应该消失，哪一条必须留下？这就是本练习的回忆与推演环节，无需额外写一份章末问答。

进入 TODO 后，确定要读取哪些字段、判断哪项条件、产生什么新值，以及怎样让旧结果的用户使用新值。API 可以从已学章节和参考工程查阅；这里暂不提供完成代码。

<details>
<summary>卡在 API 时再看定位提示</summary>

- `LabOps.h.inc` 中查 `getLowerAttr`、`getUpperAttr`，确认返回类型；常量属性与 SSA Value 是两类对象。
- 创建 arith 常量的写法可回查 `05-op-definition/ExpandClamp.cpp`，但本练习的匹配条件和目标行为不同。
- 结果替换回查 PatternRewriter 章；源码路径见 [SOURCE_READING.md](./SOURCE_READING.md)。

</details>

## 检查实现

```bash
python3 aicompiler-labs/llvm-mlir/exercises/01-clamp-simplify/check.py --stage solution
```

它会构建并显示前后 IR，再用 FileCheck 检查：正/负的相等区间、合法不匹配区间、多处使用及函数声明。多 use 用例要求两个 addi operand 和 return 都使用替换后的结果；最后还检查重复运行不再改变结果。

初始骨架运行 solution 应失败，这是待实现行为未满足的提示。请根据首个失败定位原因，不要通过删除检查、添加其他优化 Pass 或按函数名特判来绕开任务。

提供的用例没有穷举所有边界。请自己补一个零值或 i32 极值的相等区间，说明它补充检查了什么。记录输出即可，不需要长篇实验报告。这些检查验证编译器侧改写关系，尚不包含目标机器码执行。

## 源码阅读与提交审阅

可以在写代码前，或第一次遇到替换/验证疑问时，按 [SOURCE_READING.md](./SOURCE_READING.md) 查一个问题。首先读完整的本地练习函数，再读生成代码与上游中的对应函数，不必通读仓库。

完成后直接告诉我文件已修改。我会审阅条件是否充分、未匹配路径是否保持 IR、use 是否全部替换、测试有没有遗漏，并结合你的解释判断理解情况。除非你要求完整答案，练习辅导先定位问题和提供提示。

构建产物在 `artifacts/builds/mlir-exercise-clamp/`，输出、诊断和 FileCheck 结果在 `artifacts/logs/mlir-exercise-clamp/<时间>/`。固定使用工作区 LLVM/MLIR 20.1.8，详细环境见 `aicompiler-labs/environments/version-matrix.md`。
