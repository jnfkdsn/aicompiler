#include "mlir/Dialect/Affine/Analysis/AffineAnalysis.h"
#include "mlir/Dialect/Affine/IR/AffineOps.h"
#include "mlir/Dialect/Affine/LoopUtils.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/MemRef/IR/MemRef.h"
#include "mlir/Parser/Parser.h"
#include "llvm/Support/raw_ostream.h"
using namespace mlir;
int main(int argc, char **argv) {
  if (argc!=2) { llvm::errs()<<"usage: inspect-dependence input.mlir\n"; return 2; }
  DialectRegistry registry;
  registry.insert<affine::AffineDialect, arith::ArithDialect, func::FuncDialect, memref::MemRefDialect>();
  MLIRContext context(registry);
  auto module=parseSourceFile<ModuleOp>(argv[1],&context);
  if (!module) return 1;
  SmallVector<affine::AffineForOp> loops;
  module->walk<WalkOrder::PreOrder>([&](affine::AffineForOp loop){loops.push_back(loop);});
  if (loops.size()!=2 || !affine::isPerfectlyNested(loops)) {
    llvm::errs()<<"expected one perfect nest with two affine loops\n"; return 2;
  }
  SmallVector<unsigned> identity{0,1}, swap{1,0};
  llvm::outs()<<"identity legal: "<<affine::isValidLoopInterchangePermutation(loops,identity)
              <<"\nswap legal: "<<affine::isValidLoopInterchangePermutation(loops,swap)
              <<"\nouter parallel: "<<affine::isLoopParallel(loops[0])
              <<"\ninner parallel: "<<affine::isLoopParallel(loops[1])<<"\n";
  return 0;
}
