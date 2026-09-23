#include "LabOps.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/OpImplementation.h"
using namespace mlir;
using namespace mlir::lab;
#include "LabDialect.cpp.inc"
#define GET_OP_CLASSES
#include "LabOps.cpp.inc"

// BEGIN: initialize
void LabDialect::initialize() {
  addOperations<
#define GET_OP_LIST
#include "LabOps.cpp.inc"
      >();
}
// END: initialize

// BEGIN: verify
LogicalResult ClampOp::verify() {
  if (getLowerAttr().getValue().sgt(getUpperAttr().getValue()))
    return emitOpError("requires lower <= upper (signed i32)");
  return success();
}
// END: verify
