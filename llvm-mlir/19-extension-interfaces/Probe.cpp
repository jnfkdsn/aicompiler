#include "MyOps.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/Verifier.h"
#include "mlir/IR/RegionKindInterface.h"
#include "mlir/Interfaces/CallInterfaces.h"
#include "mlir/Interfaces/ControlFlowInterfaces.h"
#include "mlir/Interfaces/FunctionInterfaces.h"
#include "mlir/Interfaces/LoopLikeInterface.h"
#include "mlir/Pass/Pass.h"
using namespace mlir;
namespace {
struct Probe : PassWrapper<Probe, OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(Probe)
  StringRef getArgument() const final { return "my-probe-interfaces"; }
  StringRef getDescription() const final { return "Observe interface consumers"; }
  void runOnOperation() final {
    bool bad = false;
    getOperation().walk([&](Operation *op) {
      for (Region &region : op->getRegions())
        llvm::errs() << "region-kind " << op->getName() << "[" << region.getRegionNumber() << "] SSA=" << mayHaveSSADominance(region) << "\n";
      if (auto add = dyn_cast<my::AddOneOp>(op)) {
        // Detached construction exercises the generated builder; no IR uses
        // are replaced. The temporary operation must be destroyed explicitly.
        OpBuilder builder(op->getContext());
        OperationState state(op->getLoc(), my::AddOneOp::getOperationName());
        my::AddOneOp::build(builder, state, add.getInput(), add.getInit());
        Operation *created = Operation::create(state);
        llvm::errs() << "inferred result: " << created->getResult(0).getType() << "\n";
        bad |= failed(verify(created));
        created->destroy();
      }
      if (auto function = dyn_cast<FunctionOpInterface>(op))
        llvm::errs() << "function " << function.getName() << " arguments="
                     << function.getNumArguments() << "\n";
      if (auto callable = dyn_cast<CallableOpInterface>(op))
        llvm::errs() << "callable " << op->getName() << " body="
                     << bool(callable.getCallableRegion()) << "\n";
      if (auto call = dyn_cast<CallOpInterface>(op)) {
        Operation *callee = call.resolveCallable();
        llvm::errs() << "call " << op->getName() << " arguments="
                     << call.getArgOperands().size() << " resolved=" << bool(callee) << "\n";
      }
      if (auto loop = dyn_cast<LoopLikeOpInterface>(op))
        llvm::errs() << "loop " << op->getName() << " regions="
                     << loop.getLoopRegions().size() << "\n";
      if (auto branch = dyn_cast<RegionBranchOpInterface>(op)) {
        auto print = [&](RegionBranchPoint point, StringRef source) {
          SmallVector<RegionSuccessor> successors;
          branch.getSuccessorRegions(point, successors);
          llvm::errs() << op->getName() << " from " << source << ":";
          for (auto successor : successors) {
            if (successor.isParent()) llvm::errs() << " parent";
            else llvm::errs() << " region" << successor.getSuccessor()->getRegionNumber();
            llvm::errs() << "[" << successor.getSuccessorInputs().size() << "]";
          }
          llvm::errs() << "\n";
        };
        print(RegionBranchPoint::parent(), "parent");
        for (Region &r : op->getRegions()) print(&r, "region");
      }
    });
    if (bad) signalPassFailure();
    else markAllAnalysesPreserved();
  }
};
}
void registerMyProbe() { PassRegistration<Probe>(); }
