#include "RangeConversion.h"
#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/ControlFlow/IR/ControlFlowOps.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/Func/Transforms/FuncConversions.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Transforms/DialectConversion.h"
#include "llvm/ADT/DenseSet.h"
using namespace mlir;
namespace {
// BEGIN: converter
struct RangeTypeConverter : TypeConverter {
  RangeTypeConverter() {
    addConversion([](Type type) { return type; });
    addConversion([](my::RangeType type) -> Type {
      return IntegerType::get(type.getContext(), 32);
    });
  }
};
// END: converter

// BEGIN: limit-pattern
struct ConvertLimit : OpConversionPattern<my::LimitOp> {
  using OpConversionPattern::OpConversionPattern;
  LogicalResult matchAndRewrite(my::LimitOp op, OpAdaptor adaptor,
                               ConversionPatternRewriter &rewriter) const override {
    auto bounds = op.getBounds();
    auto lower = rewriter.create<arith::ConstantIntOp>(op.getLoc(), bounds.getLower(), 32);
    auto upper = rewriter.create<arith::ConstantIntOp>(op.getLoc(), bounds.getUpper(), 32);
    auto bounded = rewriter.create<arith::MaxSIOp>(op.getLoc(), adaptor.getInput(), lower);
    rewriter.replaceOpWithNewOp<arith::MinSIOp>(op, bounded, upper);
    return success();
  }
};
// END: limit-pattern

// BEGIN: materialize
Value materializeRangeBoundary(OpBuilder &builder, Type type,
                               ValueRange inputs, Location loc) {
  if (inputs.size() != 1)
    return {};
  Type inputType = inputs.front().getType();
  bool toRange = isa<my::RangeType>(type) && inputType.isInteger(32);
  bool toInteger = type.isInteger(32) && isa<my::RangeType>(inputType);
  if (!toRange && !toInteger)
    return {};
  return builder.create<UnrealizedConversionCastOp>(loc, type, inputs).getResult(0);
}
// END: materialize

// BEGIN: scope-pattern
struct ConvertScope : OpConversionPattern<my::ScopeOp> {
  using OpConversionPattern::OpConversionPattern;
  LogicalResult matchAndRewrite(my::ScopeOp op, OpAdaptor adaptor,
                               ConversionPatternRewriter &rewriter) const override {
    SmallVector<Type> resultTypes;
    if (failed(getTypeConverter()->convertTypes(op.getResultTypes(), resultTypes)))
      return failure();
    OperationState state(op.getLoc(), my::ScopeOp::getOperationName());
    state.addOperands(adaptor.getInputs());
    state.addTypes(resultTypes);
    state.addAttributes(op->getAttrs());
    state.addRegion();
    auto replacement = cast<my::ScopeOp>(rewriter.create(state));
    rewriter.inlineRegionBefore(op.getBody(), replacement.getBody(), replacement.getBody().end());
    if (failed(rewriter.convertRegionTypes(&replacement.getBody(), *getTypeConverter())))
      return failure();
    rewriter.replaceOp(op, replacement.getOutputs());
    return success();
  }
};
// END: scope-pattern
// BEGIN: yield-pattern
struct ConvertYield : OpConversionPattern<my::YieldOp> {
  using OpConversionPattern::OpConversionPattern;
  LogicalResult matchAndRewrite(my::YieldOp op, OpAdaptor adaptor,
                               ConversionPatternRewriter &rewriter) const override {
    rewriter.replaceOpWithNewOp<my::YieldOp>(op, adaptor.getValues());
    return success();
  }
};
// END: yield-pattern

struct ConvertRangePass : PassWrapper<ConvertRangePass, OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(ConvertRangePass)
  StringRef getArgument() const final { return "my-convert-range"; }
  void getDependentDialects(DialectRegistry &registry) const override {
    registry.insert<arith::ArithDialect>();
  }
  void runOnOperation() override {
    if (failed(convertRangeModule(getOperation()))) signalPassFailure();
  }
};
} // namespace

LogicalResult convertRangeModule(ModuleOp module, RangeConversionOptions options) {
  MLIRContext *context = module.getContext();
  RangeTypeConverter converter;
  if (options.bridges) {
    // BEGIN: register-materializations
    converter.addSourceMaterialization(materializeRangeBoundary);
    converter.addTargetMaterialization(materializeRangeBoundary);
    // END: register-materializations
  }
  ConversionTarget target(*context);
  target.addLegalOp<ModuleOp, UnrealizedConversionCastOp>();
  target.addLegalDialect<arith::ArithDialect>();
  target.addIllegalOp<my::LimitOp>();
  RewritePatternSet patterns(context);
  patterns.add<ConvertLimit>(converter, context);
  if (options.partial || options.recursive) {
    target.addLegalOp<func::FuncOp, func::ReturnOp, func::CallOp,
                      my::ScopeOp, my::YieldOp, cf::BranchOp>();
    if (options.recursive) {
      // BEGIN: recursive
      target.markOpRecursivelyLegal<func::FuncOp>();
      // END: recursive
    }
  } else {
    // BEGIN: function-target
    target.addDynamicallyLegalOp<func::FuncOp>([&](func::FuncOp op) {
      return converter.isSignatureLegal(op.getFunctionType()) &&
             converter.isLegal(&op.getBody());
    });
    target.addDynamicallyLegalOp<func::ReturnOp>([&](func::ReturnOp op) {
      return converter.isLegal(op);
    });
    // END: function-target
    // BEGIN: function-patterns
    populateFunctionOpInterfaceTypeConversionPattern<func::FuncOp>(patterns, converter);
    populateReturnOpTypeConversionPattern(patterns, converter);
    // END: function-patterns
    // BEGIN: call-target
    target.addDynamicallyLegalOp<func::CallOp>([&](func::CallOp op) {
      return converter.isLegal(op);
    });
    // END: call-target
    if (options.calls) {
      // BEGIN: call-pattern
      populateCallOpTypeConversionPattern(patterns, converter);
      // END: call-pattern
    }
    // BEGIN: region-target
    target.addDynamicallyLegalOp<my::ScopeOp>([&](my::ScopeOp op) {
      return converter.isLegal(op) && converter.isLegal(&op.getBody());
    });
    target.addDynamicallyLegalOp<my::YieldOp>([&](my::YieldOp op) {
      return converter.isLegal(op);
    });
    // END: region-target
    patterns.add<ConvertScope>(converter, context);
    if (options.yields) patterns.add<ConvertYield>(converter, context);
    target.addDynamicallyLegalOp<cf::BranchOp>([&](cf::BranchOp op) {
      return converter.isLegal(op);
    });
    populateBranchOpInterfaceTypeConversionPattern(patterns, converter);
  }
  if (options.analysis) {
    // BEGIN: analysis
    DenseSet<Operation *> legalizable;
    ConversionConfig config;
    config.legalizableOps = &legalizable;
    LogicalResult result = applyAnalysisConversion(module, target, std::move(patterns), config);
    module.walk([&](my::LimitOp op) {
      llvm::errs() << "limit_legalizable=" << legalizable.contains(op.getOperation()) << "\n";
    });
    return result;
    // END: analysis
  }
  if (options.partial)
    return applyPartialConversion(module, target, std::move(patterns));
  return applyFullConversion(module, target, std::move(patterns));
}
void registerRangeConversionPass() { PassRegistration<ConvertRangePass>(); }
