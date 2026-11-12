#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
#include "mlir/Transforms/Passes.h"
void registerMyDebugPass();
int main(int argc,char **argv){
 mlir::DialectRegistry registry;
 registry.insert<mlir::arith::ArithDialect,mlir::func::FuncDialect>();
 mlir::registerTransformsPasses();registerMyDebugPass();
 return mlir::asMainReturnCode(mlir::MlirOptMain(argc,argv,"Teaching diagnosis\n",registry));
}
