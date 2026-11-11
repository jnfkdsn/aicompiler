#include "MyOps.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/DialectImplementation.h"
using namespace mlir;
#include "MyDialect.cpp.inc"
#define GET_OP_CLASSES
#include "MyOps.cpp.inc"
void mlir::my::MyDialect::initialize(){addOperations<
#define GET_OP_LIST
#include "MyOps.cpp.inc"
>();}

LogicalResult mlir::my::PackOp::verify(){
  if(cast<TupleType>(getResult().getType()).size()!=2)return emitOpError("requires a pair of i32 values");
  return success();
}
LogicalResult mlir::my::FirstOp::verify(){
  if(cast<TupleType>(getInput().getType()).size()!=2)return emitOpError("requires a pair of i32 values");
  return success();
}
LogicalResult mlir::my::SecondOp::verify(){
  if(cast<TupleType>(getInput().getType()).size()!=2)return emitOpError("requires a pair of i32 values");
  return success();
}
