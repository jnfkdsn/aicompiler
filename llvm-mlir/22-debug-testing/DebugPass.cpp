#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/Pass/Pass.h"
using namespace mlir;
namespace {
struct Reject : PassWrapper<Reject,OperationPass<ModuleOp>> {
 MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(Reject)
 Reject()=default;
 Reject(const Reject &other):PassWrapper(other){}
 Statistic seen{this,"multiplications","Multiplications examined"};
 StringRef getArgument() const final{return "my-reject-marked-mul";}
 StringRef getDescription() const final{return "Teaching restriction: reject marked integer multiply";}
 void runOnOperation() final {
  bool bad=false;
  getOperation().walk([&](arith::MulIOp op){
    ++seen;
    if(op->hasAttr("my.trigger")) {
      op.emitError("teaching restriction: marked multiply is unsupported");bad=true;
    }
  });
  if(bad)signalPassFailure();else markAllAnalysesPreserved();
 }
};
}
void registerMyDebugPass(){PassRegistration<Reject>();}
std::unique_ptr<Pass> createMyDebugPass(){return std::make_unique<Reject>();}
