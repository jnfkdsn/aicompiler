#include "MyOps.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
int main(int argc, char **argv) {
  mlir::DialectRegistry registry;
  registry.insert<mlir::my::MyDialect, mlir::func::FuncDialect>();
  return mlir::asMainReturnCode(
      mlir::MlirOptMain(argc, argv, "My dialect: stage 01\n", registry));
}
