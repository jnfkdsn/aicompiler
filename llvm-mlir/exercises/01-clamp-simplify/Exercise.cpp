#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Transforms/WalkPatternRewriteDriver.h"
using namespace mlir;
namespace {
struct SimplifyClamp : OpRewritePattern<my::ClampOp> {
  explicit SimplifyClamp(MLIRContext *ctx) : OpRewritePattern(ctx, 1) {}
  LogicalResult matchAndRewrite(my::ClampOp op,
                               PatternRewriter &rewriter) const override {
    // TODO (learner): implement the contract described in README.md.
    // The starter deliberately matches nothing and leaves the input unchanged.
    auto lower = op.getLowerAttr();
    auto upper = op.getUpperAttr();
    if (lower != upper){
      return failure();
    }
    auto constant =
      rewriter.create<arith::ConstantOp>(op.getLoc(), lower);
    rewriter.replaceOp(op, constant.getResult());
    return success();
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
