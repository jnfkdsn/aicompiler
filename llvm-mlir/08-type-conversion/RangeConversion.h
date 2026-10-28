#ifndef MY_RANGE_CONVERSION_H
#define MY_RANGE_CONVERSION_H
#include "mlir/IR/BuiltinOps.h"
#include "mlir/Support/LogicalResult.h"
struct RangeConversionOptions {
  bool partial = false;
  bool bridges = true;
  bool calls = true;
  bool yields = true;
  bool analysis = false;
  bool recursive = false;
};
mlir::LogicalResult convertRangeModule(mlir::ModuleOp module, RangeConversionOptions options = {});
void registerRangeConversionPass();
#endif
