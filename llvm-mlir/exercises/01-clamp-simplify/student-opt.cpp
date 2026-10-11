#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
void registerExercisePass();
int main(int argc, char **argv) {
  registerExercisePass();
  mlir::DialectRegistry registry;
  registry.insert<mlir::my::MyDialect, mlir::func::FuncDialect,
                  mlir::arith::ArithDialect>();
  return mlir::asMainReturnCode(
      mlir::MlirOptMain(argc, argv, "Clamp practice tool\n", registry));
}
