#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"

void registerLabPasses();

// BEGIN: main
int main(int argc, char **argv) {
  registerLabPasses();
  mlir::DialectRegistry registry;
  registry.insert<mlir::arith::ArithDialect, mlir::func::FuncDialect,
                  mlir::scf::SCFDialect>();
  return mlir::asMainReturnCode(
      mlir::MlirOptMain(argc, argv, "MLIR learning optimizer\n", registry));
}
// END: main
