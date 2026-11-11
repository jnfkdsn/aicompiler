#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/ControlFlow/IR/ControlFlowOps.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
#include "mlir/Transforms/Passes.h"
void registerMyFlatten();
void registerMyDeclarative();
int main(int argc,char **argv){
  mlir::DialectRegistry registry;
  registry.insert<mlir::my::MyDialect,mlir::arith::ArithDialect,mlir::cf::ControlFlowDialect,mlir::func::FuncDialect>();
  registerMyFlatten();registerMyDeclarative();mlir::registerTransformsPasses();
  return mlir::asMainReturnCode(mlir::MlirOptMain(argc,argv,"1:N and declarative patterns\n",registry));
}
