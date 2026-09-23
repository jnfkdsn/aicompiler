#include "Lesson.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/DialectImplementation.h"
#include "mlir/IR/OpImplementation.h"
#include "llvm/ADT/TypeSwitch.h"
#include <limits>
using namespace mlir;
using namespace mlir::lesson;
#include "LessonDialect.cpp.inc"
#define GET_TYPEDEF_CLASSES
#include "LessonTypes.cpp.inc"
#define GET_ATTRDEF_CLASSES
#include "LessonAttrs.cpp.inc"
#include "LessonInterfaces.cpp.inc"
#define GET_OP_CLASSES
#include "LessonOps.cpp.inc"
void LessonDialect::initialize() {
 addTypes<
#define GET_TYPEDEF_LIST
#include "LessonTypes.cpp.inc"
 >();
 addAttributes<
#define GET_ATTRDEF_LIST
#include "LessonAttrs.cpp.inc"
 >();
 addOperations<
#define GET_OP_LIST
#include "LessonOps.cpp.inc"
 >();
}
static LogicalResult verifyBounds(function_ref<InFlightDiagnostic()> emitError, int64_t lower, int64_t upper) {
 if (lower < std::numeric_limits<int32_t>::min() || upper > std::numeric_limits<int32_t>::max() || lower > upper)
   return emitError() << "expected ordered bounds within signed i32 range";
 return success();
}
// BEGIN: direct-methods
LogicalResult ClampOp::verify() {
 if (getLowerAttr().getValue().sgt(getUpperAttr().getValue()))
   return emitOpError("requires lower <= upper");
 return success();
}
int64_t ClampOp::getMinimum() { return getLowerAttr().getInt(); }
int64_t ClampOp::getMaximum() { return getUpperAttr().getInt(); }
// END: direct-methods
// BEGIN: type-attr-verify
LogicalResult RangeType::verify(function_ref<InFlightDiagnostic()> emitError, int64_t lower, int64_t upper) {
 return verifyBounds(emitError, lower, upper);
}
LogicalResult BoundsAttr::verify(function_ref<InFlightDiagnostic()> emitError, int64_t lower, int64_t upper) {
 return verifyBounds(emitError, lower, upper);
}
// END: type-attr-verify
// BEGIN: limit-verify
LogicalResult LimitOp::verify() {
 auto range = getResult().getType();
 auto bounds = getBounds();
 if (range.getLower() != bounds.getLower() || range.getUpper() != bounds.getUpper())
   return emitOpError("result range must match bounds attribute");
 return success();
}
int64_t LimitOp::getMinimum() { return getBounds().getLower(); }
int64_t LimitOp::getMaximum() { return getBounds().getUpper(); }
// END: limit-verify
LogicalResult OpaqueClampOp::verify() {
 if (getLowerAttr().getValue().sgt(getUpperAttr().getValue()))
   return emitOpError("requires lower <= upper");
 return success();
}
// BEGIN: scope-verify
LogicalResult ScopeOp::verify() {
 if (getBody().empty())
   return emitOpError("requires a nonempty body");
 Block &entry = getBody().front();
 if (entry.getArgumentTypes() != getInputs().getTypes())
   return emitOpError("entry argument types must match input types");
 return success();
}
LogicalResult ScopeOp::verifyRegions() {
 Block &entry = getBody().front();
 if (entry.empty())
   return emitOpError("requires a lesson.yield terminator");
 auto yield = dyn_cast<YieldOp>(entry.back());
 if (!yield)
   return emitOpError("requires a lesson.yield terminator");
 if (yield.getValues().getTypes() != getOutputs().getTypes())
   return emitOpError("yield types must match result types");
 return success();
}
// END: scope-verify
// BEGIN: manual-format
ParseResult IdentityOp::parse(OpAsmParser &parser, OperationState &result) {
 OpAsmParser::UnresolvedOperand input;
 Type type;
 if (parser.parseKeyword("same") || parser.parseOperand(input) ||
     parser.parseOptionalAttrDict(result.attributes) || parser.parseColonType(type) ||
     parser.resolveOperand(input, type, result.operands))
   return failure();
 result.addTypes(type);
 return success();
}
void IdentityOp::print(OpAsmPrinter &printer) {
 printer << " same " << getInput();
 printer.printOptionalAttrDict((*this)->getAttrs());
 printer << " : " << getInput().getType();
}
// END: manual-format
