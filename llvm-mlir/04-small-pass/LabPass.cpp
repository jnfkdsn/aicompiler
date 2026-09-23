#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Transforms/GreedyPatternRewriteDriver.h"

using namespace mlir;

namespace {
// BEGIN: pattern
struct RemoveAddZero : OpRewritePattern<arith::AddIOp> {
  explicit RemoveAddZero(MLIRContext *context) : OpRewritePattern(context, 1) {}

  LogicalResult matchAndRewrite(arith::AddIOp op,
                               PatternRewriter &rewriter) const override {
    if (!op.getType().isSignlessInteger(32) ||
        op.getOverflowFlags() != arith::IntegerOverflowFlags::none)
      return failure();
    auto constant = op.getRhs().getDefiningOp<arith::ConstantOp>();
    if (!constant)
      return failure();
    auto value = dyn_cast<IntegerAttr>(constant.getValue());
    if (!value || !value.getValue().isZero())
      return failure();
    rewriter.replaceOp(op, op.getLhs());
    return success();
  }
};
// END: pattern

// BEGIN: pass
struct RemoveAddZeroPass
    : PassWrapper<RemoveAddZeroPass, OperationPass<func::FuncOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(RemoveAddZeroPass)

  StringRef getArgument() const final { return "lab-remove-add-zero"; }
  StringRef getDescription() const final {
    return "Remove unflagged scalar i32 additions with zero on the RHS";
  }

  void runOnOperation() override {
    func::FuncOp fn = getOperation();
    if (fn.isExternal())
      return;
    RewritePatternSet patterns(&getContext());
    patterns.add<RemoveAddZero>(&getContext());
    GreedyRewriteConfig config;
    config.fold = false;
    config.cseConstants = false;
    config.enableRegionSimplification = GreedySimplifyRegionLevel::Disabled;
    if (failed(applyPatternsGreedily(fn, std::move(patterns), config)))
      signalPassFailure();
  }
};
// END: pass
} // namespace

// BEGIN: registration
void registerLabPasses() {
  PassRegistration<RemoveAddZeroPass>();
}
// END: registration
