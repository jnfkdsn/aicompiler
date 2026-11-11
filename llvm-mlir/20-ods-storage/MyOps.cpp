#include "MyOps.h"
#include "NodeType.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/DialectImplementation.h"
#include "mlir/IR/OpImplementation.h"
#include "llvm/ADT/TypeSwitch.h"
#include <limits>
using namespace mlir;
using namespace mlir::my;
#include "MyDialect.cpp.inc"
#include "MyTypeInterfaces.cpp.inc"
#include "MyAttrInterfaces.cpp.inc"
#define GET_TYPEDEF_CLASSES
#include "MyTypes.cpp.inc"
#define GET_ATTRDEF_CLASSES
#include "MyAttrs.cpp.inc"
#define GET_OP_CLASSES
#include "MyOps.cpp.inc"
void MyDialect::initialize() {
  addTypes<NodeType>();
  addTypes<
#define GET_TYPEDEF_LIST
#include "MyTypes.cpp.inc"
  >();
  addAttributes<
#define GET_ATTRDEF_LIST
#include "MyAttrs.cpp.inc"
  >();
  addOperations<
#define GET_OP_LIST
#include "MyOps.cpp.inc"
  >();
}
LogicalResult TileType::verify(function_ref<InFlightDiagnostic()> emitError,
                               ArrayRef<int64_t> shape) {
  int64_t bytes=4;
  if (shape.empty()) return emitError() << "requires a nonempty static shape";
  for (int64_t dim : shape) {
    if (dim<=0 || dim>std::numeric_limits<int64_t>::max()/bytes)
      return emitError() << "requires positive dimensions and representable byte count";
    bytes*=dim;
  }
  return success();
}
int64_t TileType::getPayloadBytes() const {
  int64_t bytes=4;
  for (int64_t dim : getShape()) bytes*=dim;
  return bytes;
}
LogicalResult AlignmentAttr::verify(function_ref<InFlightDiagnostic()> emitError,
                                     int64_t alignment) {
  if (alignment<=0 || alignment>4096 || (alignment & (alignment-1)))
    return emitError() << "requires power-of-two alignment in [1,4096]";
  return success();
}
int64_t AlignmentAttr::getRequiredAlignment() const {return getAlignment();}
LogicalResult WeightedSumOp::verify() {
  if (getInputs().size()!=getWeights().size())
    return emitOpError("requires equal input and weight counts");
  return success();
}
LogicalResult GroupSumOp::verify() {
  if (getGroups().size()!=getNumResults())
    return emitOpError("requires one result per group");
  return success();
}
