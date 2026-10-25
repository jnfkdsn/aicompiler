# C++ 前置：源码、生成文件与程序

三篇 blog 补充正文从普通加法出发，读完第一篇再继续第二篇，不要求一次读完：

1. [一个函数怎样从源码进入程序](https://github.com/jnfkdsn/blog/blob/main/docs/notes/cpp/source_to_program.md)：声明、include、独立编译、链接与静态库。
2. [宏和生成代码怎样进入程序](https://github.com/jnfkdsn/blog/blob/main/docs/notes/cpp/generated_cpp.md)：条件包含、片段选择、实际预处理结果与最小生成器。
3. [读懂带类型参数的函数调用](https://github.com/jnfkdsn/blog/blob/main/docs/notes/cpp/template_calls.md)：类型、静态成员、模板实参与运行时调用。

正文包含完整源码、关键输出和直接命令。plain/ 保存手写加法，generated/ 保存生成器及接入代码，templates/ 保存类型参数例子。它们都是普通 C++，不依赖 MLIR 或 GPU/NPU。

环境：Linux、C++17 编译器 `c++`（GCC/Clang）、`ar`、Python 3。从 workspace 根目录运行正文命令，生成源码、目标文件和程序写到 `artifacts/builds/cpp-foundations/`。参考源码不会被命令修改。

学习观察：手写版与生成版都打印 5；模板例子打印 `add: 2` 和 `add: 3`。故意遗漏 add 的链接输入时应出现未定义引用；不选择宏时 generated.inc 不提供对应片段。

正文末尾提供预测题，可以先解释再自行修改副本。作者提供的参考实现与编译结果不计作学习者已完成任务。

维护者验证：

```bash
python3 aicompiler-labs/common/cpp-foundations/verify.py
```

脚本直接运行正文中的命令，核对源码/输出标记，并验证宏选择与模板错误。原始日志在 `artifacts/logs/cpp-foundations/`；它是文档维护入口，首次学习按正文解释推进。
