#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/ControlFlow/IR/ControlFlowOps.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/Func/Transforms/FuncConversions.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Transforms/DialectConversion.h"
using namespace mlir;
namespace {
struct Pack : OpConversionPattern<my::PackOp> {
 using OpConversionPattern::OpConversionPattern;
 LogicalResult matchAndRewrite(my::PackOp op,OneToNOpAdaptor adaptor,
                              ConversionPatternRewriter &rewriter) const override {
   SmallVector<Value> values{adaptor.getFirst().front(),adaptor.getSecond().front()};
   SmallVector<ValueRange> replacements{ValueRange(values)};
   rewriter.replaceOpWithMultiple(op,replacements);return success();
 }
};
template<class Op,unsigned index> struct Project : OpConversionPattern<Op> {
 using OpConversionPattern<Op>::OpConversionPattern;
 LogicalResult matchAndRewrite(Op op,typename OpConversionPattern<Op>::OneToNOpAdaptor adaptor,
                               ConversionPatternRewriter &rewriter) const override {
   ValueRange pair=adaptor.getInput();
   if(pair.size()!=2)return failure();
   rewriter.replaceOp(op,pair[index]);return success();
 }
};
struct Branch : OpConversionPattern<cf::BranchOp> {
 using OpConversionPattern::OpConversionPattern;
 LogicalResult matchAndRewrite(cf::BranchOp op,OneToNOpAdaptor adaptor,
                               ConversionPatternRewriter &rewriter) const override {
   SmallVector<Value> operands;
   for(ValueRange group:adaptor.getDestOperands())llvm::append_range(operands,group);
   rewriter.replaceOpWithNewOp<cf::BranchOp>(op,op.getDest(),operands);return success();
 }
};
template<bool addCalls> struct Flatten : PassWrapper<Flatten<addCalls>,OperationPass<ModuleOp>> {
 MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(Flatten)
 StringRef getArgument() const final{return addCalls ? "my-flatten-pairs" : "my-flatten-no-call";}
 StringRef getDescription() const final{return "Expand tuple<i32,i32> into two SSA values across function, call and block boundaries";}
 void getDependentDialects(DialectRegistry &r) const override{r.insert<arith::ArithDialect,cf::ControlFlowDialect,func::FuncDialect>();}
 void runOnOperation() final {
   MLIRContext *ctx=&this->getContext();TypeConverter converter;
   converter.addConversion([](Type type){return type;});
   converter.addConversion([](TupleType type,SmallVectorImpl<Type> &result)->LogicalResult {
     if(type.size()!=2 || !type.getType(0).isInteger(32) || !type.getType(1).isInteger(32))return failure();
     llvm::append_range(result,type.getTypes());return success();
   });
   RewritePatternSet patterns(ctx);
   patterns.add<Pack,Project<my::FirstOp,0>,Project<my::SecondOp,1>,Branch>(converter,ctx);
   populateFunctionOpInterfaceTypeConversionPattern<func::FuncOp>(patterns,converter);
   if constexpr(addCalls)populateCallOpTypeConversionPattern(patterns,converter);
   populateReturnOpTypeConversionPattern(patterns,converter);
   ConversionTarget target(*ctx);
   target.addLegalOp<ModuleOp>();target.addLegalDialect<arith::ArithDialect>();
   target.addIllegalDialect<my::MyDialect>();
   target.addDynamicallyLegalOp<func::FuncOp>([&](func::FuncOp op){
     return converter.isSignatureLegal(op.getFunctionType()) && converter.isLegal(&op.getBody());
   });
   target.addDynamicallyLegalOp<func::CallOp,func::ReturnOp>([&](Operation *op){return converter.isLegal(op);});
   target.addDynamicallyLegalOp<cf::BranchOp>([&](cf::BranchOp op){return converter.isLegal(op) && converter.isLegal(op.getDest()->getArgumentTypes());});
   if(failed(applyFullConversion(this->getOperation(),target,std::move(patterns))))this->signalPassFailure();
 }
};
}
void registerMyFlatten(){PassRegistration<Flatten<true>>();PassRegistration<Flatten<false>>();}
