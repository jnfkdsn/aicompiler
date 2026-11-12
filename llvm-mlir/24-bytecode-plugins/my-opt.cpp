#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
#include "mlir/Transforms/Passes.h"
using namespace mlir;
namespace {
struct Lower : PassWrapper<Lower,OperationPass<ModuleOp>>{
 MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(Lower)
 StringRef getArgument()const final{return "my-lower-shift";}
 StringRef getDescription()const final{return "Lower the current version of shift to arith";}
 void getDependentDialects(DialectRegistry &r)const override{r.insert<arith::ArithDialect>();}
 void runOnOperation()override{
  SmallVector<my::ShiftOp> work;
  getOperation().walk([&](my::ShiftOp op){work.push_back(op);});
  for(auto op:work){
#if MY_DIALECT_VERSION == 1
   auto amount=op.getBiasAttr().getInt();
#else
   auto amount=op.getOffsetAttr().getInt();
#endif
   OpBuilder b(op);auto c=b.create<arith::ConstantIntOp>(op.getLoc(),amount,32);
   auto add=b.create<arith::AddIOp>(op.getLoc(),op.getInput(),c);
   op.getResult().replaceAllUsesWith(add.getResult());op.erase();
  }
 }
};
}
int main(int argc,char **argv){
 registerTransformsPasses();PassRegistration<Lower>();
 DialectRegistry r;r.insert<my::MyDialect,arith::ArithDialect,func::FuncDialect>();
 return asMainReturnCode(MlirOptMain(argc,argv,"Versioned dialect example\n",r));
}
