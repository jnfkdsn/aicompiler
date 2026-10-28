#include "Conversion.h"
#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassRegistry.h"
using namespace mlir;

void configureClampTarget(ConversionTarget &target) {
  // BEGIN: target
  target.addLegalOp<ModuleOp, func::FuncOp, func::ReturnOp>();
  target.addLegalOp<arith::ConstantOp, arith::MaxSIOp, arith::MinSIOp>();
  target.addIllegalOp<my::ClampOp>();
  // END: target
}

namespace {
// BEGIN: pattern
struct ClampToArith : OpConversionPattern<my::ClampOp> {
  using OpConversionPattern::OpConversionPattern;

  LogicalResult matchAndRewrite(my::ClampOp op, OpAdaptor adaptor,
                               ConversionPatternRewriter &rewriter) const override {
    auto lower = rewriter.create<arith::ConstantOp>(op.getLoc(), op.getLowerAttr());
    auto upper = rewriter.create<arith::ConstantOp>(op.getLoc(), op.getUpperAttr());
    auto bounded = rewriter.create<arith::MaxSIOp>(op.getLoc(), adaptor.getInput(), lower);
    rewriter.replaceOpWithNewOp<arith::MinSIOp>(op, bounded, upper);
    return success();
  }
};
// END: pattern

struct ClampToArithPass : PassWrapper<ClampToArithPass, OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(ClampToArithPass)
  StringRef getArgument() const final { return "my-clamp-to-arith"; }
  StringRef getDescription() const final { return "Convert clamp to the declared arith target"; }
  void getDependentDialects(DialectRegistry &registry) const override {
    registry.insert<arith::ArithDialect>();
  }
  // BEGIN: pass
  void runOnOperation() override {
    ConversionTarget target(getContext());
    configureClampTarget(target);
    RewritePatternSet patterns(&getContext());
    populateClampPatterns(patterns);
    if (failed(applyFullConversion(getOperation(), target, std::move(patterns))))
      signalPassFailure();
  }
  // END: pass
};
} // namespace

void populateClampPatterns(RewritePatternSet &patterns) {
  patterns.add<ClampToArith>(patterns.getContext());
}
void registerClampConversionPass() { PassRegistration<ClampToArithPass>(); }
