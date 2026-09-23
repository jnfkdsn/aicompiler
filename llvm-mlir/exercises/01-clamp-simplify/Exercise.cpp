#include "LabOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Transforms/WalkPatternRewriteDriver.h"
using namespace mlir;
namespace {
struct SimplifyClamp : OpRewritePattern<lab::ClampOp> {
  explicit SimplifyClamp(MLIRContext *ctx) : OpRewritePattern(ctx, 1) {}
  LogicalResult matchAndRewrite(lab::ClampOp op,
                               PatternRewriter &rewriter) const override {
    // TODO (learner): implement the contract described in README.md.
    // The starter deliberately matches nothing and leaves the input unchanged.
    return failure();
  }
};
struct ExercisePass : PassWrapper<ExercisePass, OperationPass<func::FuncOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(ExercisePass)
  StringRef getArgument() const final { return "student-simplify-clamp"; }
  void getDependentDialects(DialectRegistry &registry) const override {
    registry.insert<arith::ArithDialect>();
  }
  void runOnOperation() override {
    if (getOperation().isExternal())
      return;
    RewritePatternSet patterns(&getContext());
    patterns.add<SimplifyClamp>(&getContext());
    walkAndApplyPatterns(getOperation(), FrozenRewritePatternSet(std::move(patterns)));
  }
};
} // namespace
void registerExercisePass() { PassRegistration<ExercisePass>(); }
