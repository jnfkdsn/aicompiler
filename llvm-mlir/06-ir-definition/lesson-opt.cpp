#include "Lesson.h"
#include "LabOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
#include "mlir/Transforms/Passes.h"
using namespace mlir;
namespace {
// BEGIN: external-model
struct ClampBoundsModel : lesson::StaticBounds::ExternalModel<ClampBoundsModel, lab::ClampOp> {
 int64_t getMinimum(Operation *op) const { return cast<lab::ClampOp>(op).getLowerAttr().getInt(); }
 int64_t getMaximum(Operation *op) const { return cast<lab::ClampOp>(op).getUpperAttr().getInt(); }
};
// END: external-model
struct ReportPass : PassWrapper<ReportPass, OperationPass<func::FuncOp>> {
 MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(ReportPass)
 StringRef getArgument() const final { return "lesson-report"; }
 void runOnOperation() override {
  getOperation().walk([](Operation *op) {
   if (op->getName().getDialectNamespace() != "lab" && op->getName().getDialectNamespace() != "lesson") return;
   llvm::errs() << op->getName() << " effect_interface=" << isa<MemoryEffectOpInterface>(op)
     << " speculatable=" << isSpeculatable(op) << " dead=" << isOpTriviallyDead(op);
   // BEGIN: consumer
   if (auto bounds = dyn_cast<lesson::StaticBounds>(op))
     llvm::errs() << " bounds=[" << bounds.getMinimum() << "," << bounds.getMaximum() << "]";
   else
     llvm::errs() << " bounds=unknown";
   // END: consumer
   llvm::errs() << "\n";
  });
 }
};
}
int main(int argc, char **argv) {
 registerTransformsPasses();
 PassRegistration<ReportPass>();
 DialectRegistry registry;
 registry.insert<lesson::LessonDialect, lab::LabDialect, arith::ArithDialect, func::FuncDialect>();
#ifndef OMIT_MODEL
 // BEGIN: attach
 registry.addExtension(+[](MLIRContext *context, lab::LabDialect *) {
   lab::ClampOp::attachInterface<ClampBoundsModel>(*context);
 });
 // END: attach
#endif
 return asMainReturnCode(MlirOptMain(argc, argv, "IR definition examples\n", registry));
}
