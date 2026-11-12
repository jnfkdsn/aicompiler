#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/Parser/Parser.h"
#include "mlir/Pass/PassManager.h"
#include "mlir/Pass/PassInstrumentation.h"
#include "mlir/Transforms/Passes.h"
using namespace mlir;
std::unique_ptr<Pass> createMyDebugPass();
namespace {
struct Trace : PassInstrumentation {
 void runBeforePass(Pass *pass,Operation *op) override {
  unsigned count=0;op->walk([&](Operation*){++count;});
  llvm::errs()<<"before "<<pass->getArgument()<<" operations="<<count<<"\n";
 }
 void runAfterPass(Pass *pass,Operation *) override{llvm::errs()<<"after "<<pass->getArgument()<<"\n";}
 void runAfterPassFailed(Pass *pass,Operation *) override{llvm::errs()<<"failed "<<pass->getArgument()<<"\n";}
};
}
int main(int argc,char **argv){
 if(argc!=2)return 2;
 DialectRegistry registry;registry.insert<arith::ArithDialect,func::FuncDialect>();
 MLIRContext ctx(registry);ctx.disableMultithreading();
 auto module=parseSourceFile<ModuleOp>(argv[1],&ctx);if(!module)return 2;
 PassManager pm(&ctx);pm.addInstrumentation(std::make_unique<Trace>());
 pm.addPass(createCanonicalizerPass());pm.addPass(createMyDebugPass());
 bool failedPipeline=failed(pm.run(*module));module->print(llvm::outs());return failedPipeline?1:0;
}
