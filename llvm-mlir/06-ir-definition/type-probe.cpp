#include "Lesson.h"
#include "mlir/IR/Builders.h"
#include "llvm/Support/raw_ostream.h"
using namespace mlir;
int main() {
 MLIRContext context;
 context.loadDialect<lesson::LessonDialect>();
 // BEGIN: uniquing
 auto a = lesson::RangeType::get(&context, -4, 7);
 auto b = lesson::RangeType::get(&context, -4, 7);
 auto c = lesson::RangeType::get(&context, -4, 8);
 llvm::outs() << "same_parameters=" << (a == b) << " different_parameters=" << (a == c) << "\n";
 // END: uniquing
 // BEGIN: checked-construction
 auto invalid = lesson::RangeType::getChecked(
     [&]() { return emitError(UnknownLoc::get(&context)); }, &context, int64_t(8), int64_t(7));
 llvm::outs() << "invalid_is_null=" << !invalid << "\n";
 // END: checked-construction
 return invalid ? 1 : 0;
}
