#include "MyOps.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/OpImplementation.h"
using namespace mlir;
using namespace mlir::my;
#include "MyDialect.cpp.inc"
#define GET_OP_CLASSES
#include "MyOps.cpp.inc"

void MyDialect::initialize() {
  addOperations<
#define GET_OP_LIST
#include "MyOps.cpp.inc"
      >();
}
