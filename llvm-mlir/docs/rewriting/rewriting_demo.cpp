#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/IR/Verifier.h"
#include "mlir/Parser/Parser.h"
#include "mlir/Rewrite/FrozenRewritePatternSet.h"
#include "mlir/Transforms/GreedyPatternRewriteDriver.h"
#include "mlir/Transforms/WalkPatternRewriteDriver.h"
#include "llvm/Support/raw_ostream.h"

using namespace mlir;

static bool isIntegerConstant(Value value, int64_t expected) {
  auto op = value.getDefiningOp<arith::ConstantOp>();
  auto attr = op ? dyn_cast<IntegerAttr>(op.getValue()) : IntegerAttr();
  return attr && attr.getValue() == expected;
}

// BEGIN: zero
struct RemoveAddZero : OpRewritePattern<arith::AddIOp> {
  explicit RemoveAddZero(MLIRContext *context)
      : OpRewritePattern(context, /*benefit=*/1) {
    setDebugName("RemoveAddZero");
  }
  LogicalResult matchAndRewrite(arith::AddIOp op,
                               PatternRewriter &rewriter) const override {
    if (!op.getType().isSignlessInteger(32) ||
        op.getOverflowFlags() != arith::IntegerOverflowFlags::none)
      return rewriter.notifyMatchFailure(op, "expected unflagged scalar i32");
    if (!isIntegerConstant(op.getRhs(), 0))
      return rewriter.notifyMatchFailure(op, "RHS is not an integer zero constant");
    llvm::errs() << "APPLY RemoveAddZero\n";
    rewriter.replaceOp(op, op.getLhs());
    return success();
  }
};
// END: zero

// BEGIN: double
struct DoubleToMul : OpRewritePattern<arith::AddIOp> {
  explicit DoubleToMul(MLIRContext *context, unsigned benefit = 1)
      : OpRewritePattern(context, benefit) {
    setDebugName("DoubleToMul");
  }
  LogicalResult matchAndRewrite(arith::AddIOp op,
                               PatternRewriter &rewriter) const override {
    if (!op.getType().isSignlessInteger(32) ||
        op.getOverflowFlags() != arith::IntegerOverflowFlags::none ||
        op.getLhs() != op.getRhs())
      return failure();
    llvm::errs() << "APPLY DoubleToMul\n";
    auto two = rewriter.create<arith::ConstantIntOp>(op.getLoc(), 2, 32);
    auto mul = rewriter.create<arith::MulIOp>(op.getLoc(), op.getLhs(), two);
    rewriter.replaceOp(op, mul.getResult());
    return success();
  }
};
// END: double

// BEGIN: shift
struct MulTwoToShift : OpRewritePattern<arith::MulIOp> {
  explicit MulTwoToShift(MLIRContext *context) : OpRewritePattern(context, 1) {
    setDebugName("MulTwoToShift");
  }
  LogicalResult matchAndRewrite(arith::MulIOp op,
                               PatternRewriter &rewriter) const override {
    if (!op.getType().isSignlessInteger(32) ||
        op.getOverflowFlags() != arith::IntegerOverflowFlags::none ||
        !isIntegerConstant(op.getRhs(), 2))
      return failure();
    llvm::errs() << "APPLY MulTwoToShift\n";
    auto one = rewriter.create<arith::ConstantIntOp>(op.getLoc(), 1, 32);
    rewriter.replaceOpWithNewOp<arith::ShLIOp>(op, op.getLhs(), one);
    return success();
  }
};
// END: shift

// BEGIN: inplace
struct MoveZeroToRhs : OpRewritePattern<arith::AddIOp> {
  explicit MoveZeroToRhs(MLIRContext *context) : OpRewritePattern(context, 1) {
    setDebugName("MoveZeroToRhs");
  }
  LogicalResult matchAndRewrite(arith::AddIOp op,
                               PatternRewriter &rewriter) const override {
    if (!op.getType().isSignlessInteger(32) ||
        op.getOverflowFlags() != arith::IntegerOverflowFlags::none ||
        !isIntegerConstant(op.getLhs(), 0) || isIntegerConstant(op.getRhs(), 0))
      return failure();
    Value lhs = op.getLhs(), rhs = op.getRhs();
    llvm::errs() << "APPLY MoveZeroToRhs\n";
    rewriter.modifyOpInPlace(op, [&] { op->setOperands(ValueRange{rhs, lhs}); });
    return success();
  }
};
// END: inplace

struct DoubleToShift : OpRewritePattern<arith::AddIOp> {
  DoubleToShift(MLIRContext *ctx, unsigned benefit) : OpRewritePattern(ctx, benefit) {
    setDebugName("DoubleToShift");
  }
  LogicalResult matchAndRewrite(arith::AddIOp op, PatternRewriter &r) const override {
    if (!op.getType().isSignlessInteger(32) ||
        op.getOverflowFlags() != arith::IntegerOverflowFlags::none ||
        op.getLhs() != op.getRhs())
      return failure();
    llvm::errs() << "APPLY DoubleToShift\n";
    auto one = r.create<arith::ConstantIntOp>(op.getLoc(), 1, 32);
    r.replaceOpWithNewOp<arith::ShLIOp>(op, op.getLhs(), one);
    return success();
  }
};

// Deliberately conflicts with DoubleToMul; run only with finite rewrite limits.
struct MulTwoToDouble : OpRewritePattern<arith::MulIOp> {
  explicit MulTwoToDouble(MLIRContext *ctx) : OpRewritePattern(ctx, 1) {
    setDebugName("MulTwoToDouble");
  }
  LogicalResult matchAndRewrite(arith::MulIOp op, PatternRewriter &r) const override {
    if (!op.getType().isSignlessInteger(32) ||
        op.getOverflowFlags() != arith::IntegerOverflowFlags::none ||
        !isIntegerConstant(op.getRhs(), 2))
      return failure();
    llvm::errs() << "APPLY MulTwoToDouble\n";
    r.replaceOpWithNewOp<arith::AddIOp>(op, op.getLhs(), op.getLhs());
    return success();
  }
};

// BEGIN: single-driver
static void applyAddZero(func::FuncOp fn, MLIRContext &context) {
  RewritePatternSet patterns(&context);
  patterns.add<RemoveAddZero>(&context);
  FrozenRewritePatternSet frozen(std::move(patterns));
  walkAndApplyPatterns(fn, frozen);
}
// END: single-driver

int main(int argc, char **argv) {
  if (argc != 3) {
    llvm::errs() << "usage: rewriting-demo MODE input.mlir\n";
    return 1;
  }
  StringRef mode(argv[1]);
  if (mode != "greedy" && mode != "walk" && mode != "fold-only" &&
      mode != "empty" && mode != "prefer-shift" && mode != "prefer-mul" &&
      mode != "cycle" && mode != "in-place" && mode != "single")
    return 1;
  DialectRegistry registry;
  registry.insert<arith::ArithDialect, func::FuncDialect>();
  MLIRContext context(registry);
  context.loadDialect<arith::ArithDialect, func::FuncDialect>();
  auto module = parseSourceFile<ModuleOp>(argv[2], &context);
  if (!module || failed(verify(module->getOperation())))
    return 1;
  auto fn = module->lookupSymbol<func::FuncOp>("twice");
  if (!fn || fn.isExternal())
    return 1;
  RewritePatternSet patterns(&context);
  if (mode == "greedy" || mode == "walk") {
    // BEGIN: population
    patterns.add<RemoveAddZero, DoubleToMul, MulTwoToShift>(&context);
    // END: population
  } else if (mode == "prefer-shift" || mode == "prefer-mul") {
    patterns.add<DoubleToMul>(&context, mode == "prefer-mul" ? 2 : 1);
    patterns.add<DoubleToShift>(&context, mode == "prefer-shift" ? 2 : 1);
  } else if (mode == "cycle") {
    patterns.add<DoubleToMul, MulTwoToDouble>(&context);
  } else if (mode == "in-place") {
    patterns.add<MoveZeroToRhs, RemoveAddZero>(&context);
  }
  FrozenRewritePatternSet frozen(std::move(patterns));
  bool changed = false;
  LogicalResult result = success();
  if (mode == "single") {
    applyAddZero(fn, context);
    llvm::errs() << "driver=walk; single traversal completed\n";
  } else if (mode == "walk") {
    walkAndApplyPatterns(fn, frozen);
    llvm::errs() << "driver=walk; single traversal completed\n";
  } else {
    // BEGIN: driver
    GreedyRewriteConfig config;
    config.fold = false;
    config.cseConstants = false;
    config.enableRegionSimplification = GreedySimplifyRegionLevel::Disabled;
    // END: driver
    if (mode == "fold-only")
      config.fold = true;
    if (mode == "cycle") {
      config.maxIterations = 2;
      config.maxNumRewrites = 4;
    }
    // BEGIN: apply
    result = applyPatternsGreedily(fn, frozen, config, &changed);
    llvm::errs() << "converged=" << succeeded(result)
                 << " changed=" << changed << "\n";
    // END: apply
  }
  if (failed(verify(module->getOperation())))
    return 3;
  module->print(llvm::outs());
  llvm::outs() << "\n";
  return failed(result) ? 2 : 0;
}
