#include "LabOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Transforms/WalkPatternRewriteDriver.h"
using namespace mlir;
namespace {
// BEGIN: expand
struct ExpandClamp : OpRewritePattern<lab::ClampOp> {
  explicit ExpandClamp(MLIRContext *context) : OpRewritePattern(context, 1) {}
  LogicalResult matchAndRewrite(lab::ClampOp op,
                               PatternRewriter &rewriter) const override {
    auto lower = rewriter.create<arith::ConstantOp>(op.getLoc(), op.getLowerAttr());
    auto upper = rewriter.create<arith::ConstantOp>(op.getLoc(), op.getUpperAttr());
    auto bounded = rewriter.create<arith::MaxSIOp>(op.getLoc(), op.getInput(), lower);
    rewriter.replaceOpWithNewOp<arith::MinSIOp>(op, bounded, upper);
    return success();
  }
};
// END: expand
struct ExpandClampPass : PassWrapper<ExpandClampPass, OperationPass<func::FuncOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(ExpandClampPass)
  StringRef getArgument() const final { return "lab-expand-clamp"; }
  StringRef getDescription() const final { return "Expand lab.clamp into signed arith min/max"; }
  void getDependentDialects(DialectRegistry &registry) const override {
    registry.insert<arith::ArithDialect>();
  }
  void runOnOperation() override {
    if (getOperation().isExternal())
      return;
    RewritePatternSet patterns(&getContext());
    patterns.add<ExpandClamp>(&getContext());
    walkAndApplyPatterns(getOperation(), FrozenRewritePatternSet(std::move(patterns)));
  }
};
}
void registerLabExpansion() { PassRegistration<ExpandClampPass>(); }
