#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Arith/Transforms/BufferizableOpInterfaceImpl.h"
#include "mlir/Dialect/Bufferization/IR/Bufferization.h"
#include "mlir/Dialect/Bufferization/Transforms/FuncBufferizableOpInterfaceImpl.h"
#include "mlir/Dialect/Bufferization/Transforms/Passes.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/Func/Extensions/AllExtensions.h"
#include "mlir/Dialect/MemRef/IR/MemRef.h"
#include "mlir/Dialect/MemRef/Transforms/Passes.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/Dialect/Tensor/IR/Tensor.h"
#include "mlir/Dialect/Tensor/Transforms/BufferizableOpInterfaceImpl.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"
#include "mlir/Transforms/Passes.h"
void registerMyProbe();
int main(int argc, char **argv) {
  mlir::DialectRegistry registry;
  registry.insert<mlir::my::MyDialect, mlir::arith::ArithDialect,
      mlir::bufferization::BufferizationDialect, mlir::func::FuncDialect,
      mlir::memref::MemRefDialect, mlir::scf::SCFDialect, mlir::tensor::TensorDialect>();
  mlir::func::registerAllExtensions(registry);
  mlir::arith::registerBufferizableOpInterfaceExternalModels(registry);
  mlir::tensor::registerBufferizableOpInterfaceExternalModels(registry);
  mlir::bufferization::func_ext::registerBufferizableOpInterfaceExternalModels(registry);
#ifndef OMIT_BUFFER_MODEL
  registerMyBufferization(registry);
#endif
  mlir::bufferization::registerBufferizationPasses();
  mlir::registerTransformsPasses();
  registerMyProbe();
  mlir::memref::registerMemRefPasses();
  return mlir::asMainReturnCode(mlir::MlirOptMain(argc, argv, "Extension interfaces\n", registry));
}
