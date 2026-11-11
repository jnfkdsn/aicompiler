#include "MyOps.h"
#include "mlir/Dialect/PDL/IR/PDL.h"
#include "mlir/Dialect/PDLInterp/IR/PDLInterp.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/Matchers.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/Parser/Parser.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Transforms/GreedyPatternRewriteDriver.h"
#include "llvm/Support/CommandLine.h"
using namespace mlir;
namespace {
llvm::cl::opt<std::string> pdlFile("my-pdl-file",llvm::cl::desc("PDL module produced from patterns.pdll"),llvm::cl::init(""));
#include "MyPatterns.inc"
struct DRR : PassWrapper<DRR,OperationPass<ModuleOp>> {
 MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(DRR)
 StringRef getArgument() const final{return "my-apply-drr";}
 StringRef getDescription() const final{return "Apply generated x+0 pattern";}
 void runOnOperation() final {
  RewritePatternSet patterns(&getContext());populateWithGenerated(patterns);
  if(failed(applyPatternsGreedily(getOperation(),std::move(patterns))))signalPassFailure();
 }
};
struct PDLL : PassWrapper<PDLL,OperationPass<ModuleOp>> {
 MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(PDLL)
 StringRef getArgument() const final{return "my-apply-pdl";}
 StringRef getDescription() const final{return "Load PDL and use the same x+0 constraint";}
 void getDependentDialects(DialectRegistry &r) const override{r.insert<pdl::PDLDialect,pdl_interp::PDLInterpDialect>();}
 void runOnOperation() final {
  auto module=parseSourceFile<ModuleOp>(pdlFile,&getContext());
  if(!module){signalPassFailure();return;}
  PDLPatternModule pdl(std::move(module));
  pdl.registerConstraintFunction("IsZero",[](PatternRewriter &,Value v){return success(matchPattern(v,m_Zero()));});
  RewritePatternSet patterns(&getContext());patterns.add(std::move(pdl));
  if(failed(applyPatternsGreedily(getOperation(),std::move(patterns))))signalPassFailure();
 }
};
}
void registerMyDeclarative(){PassRegistration<DRR>();PassRegistration<PDLL>();}
