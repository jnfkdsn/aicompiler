// Observation configurations share the production pattern and target.
#include "Conversion.h"
#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/Verifier.h"
#include "mlir/Parser/Parser.h"
#include "llvm/Support/raw_ostream.h"
using namespace mlir;
int main(int argc, char **argv) {
  if (argc != 3) {
    llvm::errs() << "usage: conversion-probe MODE input.mlir\n";
    return 2;
  }
  StringRef mode = argv[1];
  if (mode != "full" && mode != "partial" && mode != "full-no-rule" &&
      mode != "partial-no-rule" && mode != "full-no-constant" &&
      mode != "partial-no-constant" && mode != "full-dynamic" &&
      mode != "partial-dynamic") {
    llvm::errs() << "unknown observation mode\n";
    return 2;
  }
  DialectRegistry registry;
  registry.insert<my::MyDialect, arith::ArithDialect, func::FuncDialect>();
  MLIRContext context(registry);
  // Unlike PassManager, this standalone driver has no getDependentDialects hook.
  context.getOrLoadDialect<arith::ArithDialect>();
  auto module = parseSourceFile<ModuleOp>(argv[2], &context);
  if (!module || failed(verify(*module))) return 2;
  ConversionTarget target(context);
  if (mode.ends_with("-no-constant")) {
    // Deliberately leave newly created arith.constant unknown to this target.
    target.addLegalOp<ModuleOp, func::FuncOp, func::ReturnOp,
                      arith::MaxSIOp, arith::MinSIOp>();
    target.addIllegalOp<my::ClampOp>();
  } else {
    configureClampTarget(target);
  }
  if (mode.ends_with("-dynamic")) {
    // BEGIN: dynamic-target
    target.addDynamicallyLegalOp<arith::MaxSIOp>([](arith::MaxSIOp op) {
      return op.getType().isInteger(32);
    });
    // END: dynamic-target
  }
  RewritePatternSet patterns(&context);
  if (!mode.ends_with("-no-rule")) populateClampPatterns(patterns);
  LogicalResult result = mode.starts_with("partial")
      ? applyPartialConversion(*module, target, std::move(patterns))
      : applyFullConversion(*module, target, std::move(patterns));
  if (failed(result)) {
    llvm::errs() << "conversion=failed\n";
    return 1;
  }
  if (failed(verify(*module))) return 2;
  llvm::errs() << "conversion=success\n";
  module->print(llvm::outs());
  llvm::outs() << "\n";
  return 0;
}
