#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
#include "mlir/Transforms/Passes.h"
void registerMySegments();
int main(int argc,char **argv) {
  mlir::DialectRegistry registry;
  registry.insert<mlir::my::MyDialect,mlir::arith::ArithDialect,mlir::func::FuncDialect>();
  mlir::registerTransformsPasses();
  registerMySegments();
  return mlir::asMainReturnCode(mlir::MlirOptMain(argc,argv,"ODS storage\n",registry));
}
