#include "Conversion.h"
#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
int main(int argc, char **argv) {
  registerClampConversionPass();
  mlir::DialectRegistry registry;
  registry.insert<mlir::my::MyDialect, mlir::arith::ArithDialect,
                  mlir::func::FuncDialect>();
  return mlir::asMainReturnCode(
      mlir::MlirOptMain(argc, argv, "Clamp dialect conversion\n", registry));
}
