#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/Pass/Pass.h"
using namespace mlir;
namespace {
struct Inspect : PassWrapper<Inspect,OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(Inspect)
  StringRef getArgument() const final {return "my-inspect-segments";}
  StringRef getDescription() const final {return "Show operand groups and property storage";}
  void runOnOperation() final {
    getOperation().walk([](my::WeightedSumOp op) {
      llvm::errs()<<"weighted groups="<<op.getInputs().size()<<","<<op.getWeights().size()<<","<<bool(op.getSeed())<<"\n";
      llvm::errs()<<"properties="<<op->getPropertiesAsAttribute()<<" discardable="<<op->getDiscardableAttrDictionary()<<"\n";
    });
    getOperation().walk([](my::GroupSumOp op) {
      llvm::errs()<<"nested groups:";
      for (OperandRange group : op.getGroups()) llvm::errs()<<" "<<group.size();
      llvm::errs()<<"\n";
    });
    markAllAnalysesPreserved();
  }
};
struct Append : PassWrapper<Append,OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(Append)
  StringRef getArgument() const final {return "my-append-pair";}
  StringRef getDescription() const final {return "Append one existing input/weight pair with sized mutable accessors";}
  void runOnOperation() final {
    getOperation().walk([](my::WeightedSumOp op) {
      if(op.getInputs().empty())return;
      Value input=op.getInputs().front(),weight=op.getWeights().front();
      op.getInputsMutable().append(input);
      op.getWeightsMutable().append(weight);
    });
  }
};
struct Lower : PassWrapper<Lower,OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(Lower)
  StringRef getArgument() const final {return "my-lower-sums";}
  StringRef getDescription() const final {return "Consume semantic groups and lower to scalar i32 arithmetic";}
  void getDependentDialects(DialectRegistry &r) const override {r.insert<arith::ArithDialect>();}
  void runOnOperation() final {
    IRRewriter rewriter(&getContext());
    getOperation().walk([&](my::WeightedSumOp op) {
      rewriter.setInsertionPoint(op);
      Value acc=op.getSeed();
      if(!acc)acc=rewriter.create<arith::ConstantIntOp>(op.getLoc(),0,32);
      for(auto pair:llvm::zip(op.getInputs(),op.getWeights())) {
        Value product=rewriter.create<arith::MulIOp>(op.getLoc(),std::get<0>(pair),std::get<1>(pair));
        acc=rewriter.create<arith::AddIOp>(op.getLoc(),acc,product);
      }
      rewriter.replaceOp(op,acc);
    });
    getOperation().walk([&](my::GroupSumOp op) {
      rewriter.setInsertionPoint(op);SmallVector<Value> results;
      for(OperandRange group:op.getGroups()) {
        Value acc=rewriter.create<arith::ConstantIntOp>(op.getLoc(),0,32);
        for(Value v:group)acc=rewriter.create<arith::AddIOp>(op.getLoc(),acc,v);
        results.push_back(acc);
      }
      rewriter.replaceOp(op,results);
    });
  }
};
}
void registerMySegments() {PassRegistration<Inspect>();PassRegistration<Append>();PassRegistration<Lower>();}
