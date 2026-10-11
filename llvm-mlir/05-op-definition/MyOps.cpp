#include "MyOps.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/OpImplementation.h"
using namespace mlir;
using namespace mlir::my;
#include "MyDialect.cpp.inc"
#define GET_OP_CLASSES
#include "MyOps.cpp.inc"

// BEGIN: initialize
void MyDialect::initialize() {
  addOperations<
#define GET_OP_LIST
#include "MyOps.cpp.inc"
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
