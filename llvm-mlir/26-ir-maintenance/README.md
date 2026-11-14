# 26：区域协议、IR维护与有限源码链

本工程补齐三个相邻观察：SCF结果如何进入CFG/CPU；复杂函数复制、符号改名和移动需要维护哪些关系；一条标准算术fold怎样被框架消费。它们各有独立输入，不要求把所有概念塞进一个Pass。

## 构建和观察

```bash
cmake -G Ninja -S aicompiler-labs/llvm-mlir/26-ir-maintenance \
  -B artifacts/builds/mlir-ir-maintenance \
  -DMLIR_DIR="$PWD/artifacts/builds/mlir-20.1.8/lib/cmake/mlir" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=/usr/bin/clang \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++
cmake --build artifacts/builds/mlir-ir-maintenance -j 2
artifacts/builds/mlir-ir-maintenance/inspect \
  aicompiler-labs/llvm-mlir/26-ir-maintenance/maintenance.mlir
artifacts/builds/mlir-20.1.8/bin/mlir-opt \
  aicompiler-labs/llvm-mlir/26-ir-maintenance/scf_regions.mlir --convert-scf-to-cf
python3 aicompiler-labs/llvm-mlir/26-ir-maintenance/observe.py
python3 aicompiler-labs/llvm-mlir/docs/validate_maintenance.py
```

inspect预期打印一次非法移动的支配诊断，然后移回并验证成功。它不执行非法IR。完整observe还打印分阶段IR、17个正确范围内CPU用例、独立标注的宽标签版本限制及7个有限源码入口。

## 证据和限制

- clone映射4个Block/参数/分支目标/嵌套捕获；SymbolRef @leaf仍为原符号；rename更新caller。
- 对未知潜在SymbolTable，在body Region查询使用者，应用程序保护条件拒绝改名。不是宣称所有版本rename自动提供该保护。
- 真实memref.copy的read/write都是stage0/full；alloca资源是AutomaticAllocationScope。单独synthetic protocol构造stage0→1和TeachingCounter，只演示协议，不伪装成某操作的实际效果。
- 多出口execute_region合法并能转CF，但本版本One-Shot要求unique yield；两条编译子链分开。
- SCF parallel/forall的CPU结果来自串行参考lowering，未验证设备并行。
- **已知版本限制**：20.1.8 IndexSwitchLowering将index截为i32。正确性用例限定有符号32位tag；宽tag4294967296实测得到7，而源default应为6。manifest把它记录为已知限制观察，不能计入正确转换用例。真实项目需限制范围或改用保持完整宽度的合法化路径。

## 有限练习

1. 将多出口execute_region改为内部合流和唯一yield，预测bufferization行为。
2. forall只更新偶数位置，以有效初值替代empty，解释剩余位置。
3. 新增只在yes使用的常量，比较合法移入yes与当前one非法移动。
4. 沿reading_source.py给出的7个入口解释x+0→x，再用未知y说明conversion与fold的区别。

所有新代码/命令/输出保存在artifacts/logs/mlir-docs/*-ir-maintenance。LLVM固定20.1.8；生成.inc来自同次构建，不复制或手改上游生成物。
