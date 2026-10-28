#include "RangeConversion.h"
#include "MyOps.h"
#include "mlir/Conversion/ReconcileUnrealizedCasts/ReconcileUnrealizedCasts.h"
#include "mlir/Pass/PassRegistry.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/ControlFlow/IR/ControlFlowOps.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
#include "mlir/Transforms/Passes.h"
int main(int argc, char **argv) {
  registerRangeConversionPass();
  mlir::registerTransformsPasses();
  mlir::registerPass([] { return mlir::createReconcileUnrealizedCastsPass(); });
  mlir::DialectRegistry registry;
  registry.insert<mlir::my::MyDialect, mlir::arith::ArithDialect,
                  mlir::func::FuncDialect, mlir::cf::ControlFlowDialect>();
  return mlir::asMainReturnCode(mlir::MlirOptMain(argc, argv, "Range conversion\n", registry));
}
