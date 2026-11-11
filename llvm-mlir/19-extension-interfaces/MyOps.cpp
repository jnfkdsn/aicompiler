#include "MyOps.h"
#include "mlir/Dialect/Tensor/IR/Tensor.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/DialectImplementation.h"
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
LogicalResult AddOneOp::verify() {
  if (getInput().getType().getRank() != 1)
    return emitOpError("requires a rank-one f32 tensor");
  return success();
}
// SameOperandsAndResultType lets ODS generate inferReturnTypes. Runtime shape
// values are a separate interface: an unknown dimension becomes tensor.dim.
LogicalResult AddOneOp::reifyResultShapes(OpBuilder &builder,
                                         ReifiedRankedShapedTypeDims &shapes) {
  auto type = getInput().getType();
  if (type.isDynamicDim(0))
    shapes.push_back({builder.create<tensor::DimOp>(getLoc(), getInput(), 0).getResult()});
  else
    shapes.push_back({builder.getIndexAttr(type.getDimSize(0))});
  return success();
}

OperandRange ScopeOp::getEntrySuccessorOperands(RegionBranchPoint point) {
  return getOperation()->getOperands();
}
void ScopeOp::getSuccessorRegions(RegionBranchPoint point,
                                  SmallVectorImpl<RegionSuccessor> &successors) {
  if (point.isParent())
    successors.emplace_back(&getBody(), getBody().empty() ? Block::BlockArgListType{} : getBody().front().getArguments());
  else
    successors.emplace_back(getOperation()->getResults());
}
LogicalResult ScopeOp::verifyRegions() {
  if (getBody().empty() || getBody().front().getNumArguments() != 1 ||
      !getBody().front().getArgument(0).getType().isInteger(32))
    return emitOpError("requires one i32 entry argument");
  if (!isa<YieldOp>(getBody().front().getTerminator()))
    return emitOpError("requires my.yield");
  return success();
}
