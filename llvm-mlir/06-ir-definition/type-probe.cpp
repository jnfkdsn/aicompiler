#include "MyOps.h"
#include "mlir/IR/Builders.h"
#include "llvm/Support/raw_ostream.h"
using namespace mlir;
int main() {
 MLIRContext context;
 context.loadDialect<my::MyDialect>();
 // BEGIN: uniquing
 auto a = my::RangeType::get(&context, -4, 7);
 auto b = my::RangeType::get(&context, -4, 7);
 auto c = my::RangeType::get(&context, -4, 8);
 llvm::outs() << "same_parameters=" << (a == b) << " different_parameters=" << (a == c) << "\n";
 // END: uniquing
 // BEGIN: checked-construction
 auto invalid = my::RangeType::getChecked(
     [&]() { return emitError(UnknownLoc::get(&context)); }, &context, int64_t(8), int64_t(7));
 llvm::outs() << "invalid_is_null=" << !invalid << "\n";
 // END: checked-construction
 return invalid ? 1 : 0;
}
