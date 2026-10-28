#include "RangeConversion.h"
#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/ControlFlow/IR/ControlFlowOps.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/Verifier.h"
#include "mlir/Parser/Parser.h"
#include "mlir/Transforms/DialectConversion.h"
#include "llvm/Support/raw_ostream.h"
using namespace mlir;
int main(int argc, char **argv) {
  if (argc != 3) { llvm::errs() << "usage: range-probe MODE input.mlir\n"; return 2; }
  StringRef mode = argv[1];
  if (mode != "full" && mode != "partial" && mode != "partial-no-bridge" &&
      mode != "full-no-bridge" && mode != "no-call" && mode != "no-yield" &&
      mode != "analysis" && mode != "recursive" && mode != "finish") return 2;
  DialectRegistry registry;
  registry.insert<my::MyDialect, arith::ArithDialect, func::FuncDialect, cf::ControlFlowDialect>();
  MLIRContext context(registry);
  context.getOrLoadDialect<arith::ArithDialect>();
  auto module = parseSourceFile<ModuleOp>(argv[2], &context);
  if (!module || failed(verify(*module))) return 2;
  RangeConversionOptions options;
  options.partial = mode.starts_with("partial");
  options.bridges = !mode.ends_with("no-bridge");
  options.calls = mode != "no-call";
  options.yields = mode != "no-yield";
  options.analysis = mode == "analysis";
  options.recursive = mode == "recursive";
  if (failed(convertRangeModule(*module, options))) return 1;
  if (mode == "finish") {
    SmallVector<UnrealizedConversionCastOp> casts, remaining;
    module->walk([&](UnrealizedConversionCastOp op) { casts.push_back(op); });
    reconcileUnrealizedCasts(casts, &remaining);
    if (!remaining.empty()) { llvm::errs() << "unresolved boundary remains\n"; return 1; }
  }
  if (failed(verify(*module))) return 2;
  module->print(llvm::outs());
  llvm::outs() << "\n";
  return 0;
}
