#include "mlir/Analysis/AliasAnalysis.h"
#include "mlir/Analysis/CallGraph.h"
#include "mlir/Analysis/DataFlow/ConstantPropagationAnalysis.h"
#include "mlir/Analysis/DataFlow/DeadCodeAnalysis.h"
#include "mlir/Analysis/DataFlow/IntegerRangeAnalysis.h"
#include "mlir/Analysis/Liveness.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/ControlFlow/IR/ControlFlowOps.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/MemRef/IR/MemRef.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/IR/Dominance.h"
#include "mlir/IR/Verifier.h"
#include "mlir/Parser/Parser.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Pass/PassManager.h"
#include "llvm/Support/raw_ostream.h"
#include <string>

using namespace mlir;

static unsigned countOperations(Operation *op) {
  unsigned count = 0;
  op->walk([&](Operation *) { ++count; });
  return count;
}

struct OperationCount {
  explicit OperationCount(Operation *op)
      : count(countOperations(op)) {
    // Construction is printed only to make this teaching analysis observable.
    llvm::outs() << "build OperationCount=" << count << "\n";
  }
  unsigned count;
};

struct ReportCount : PassWrapper<ReportCount, OperationPass<func::FuncOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(ReportCount)
  void runOnOperation() override {
    auto &cached = getAnalysis<OperationCount>();
    unsigned fresh = countOperations(getOperation());
    llvm::outs() << "report cached=" << cached.count
                 << " fresh=" << fresh << " stale=" << (cached.count != fresh)
                 << "\n";
    markAllAnalysesPreserved();
  }
};

struct AddConstant : PassWrapper<AddConstant, OperationPass<func::FuncOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(AddConstant)
  explicit AddConstant(bool incorrectPreserve = false)
      : incorrectPreserve(incorrectPreserve) {}
  AddConstant(const AddConstant &) = default;
  void runOnOperation() override {
    func::FuncOp func = getOperation();
    OpBuilder builder(func.getBody().front().getTerminator());
    builder.create<arith::ConstantIntOp>(func.getLoc(), 99, 32);
    // Deliberately wrong option for the negative demonstration: verify(IR)
    // cannot detect that a private cached integer is now stale.
    if (incorrectPreserve)
      markAnalysesPreserved<OperationCount>();
  }
  bool incorrectPreserve;
};

static void inspectDominance(ModuleOp module) {
  auto func = module.lookupSymbol<func::FuncOp>("choose");
  SmallVector<arith::AddIOp> adds;
  func.walk([&](arith::AddIOp op) { adds.push_back(op); });
  scf::IfOp branch;
  func.walk([&](scf::IfOp op) { branch = op; });
  auto ret = func.getBody().front().getTerminator();
  DominanceInfo dominance(func);
  Liveness liveness(func);
  llvm::outs() << "base dominates local: "
               << dominance.dominates(adds[0].getResult(), adds[1]) << "\n"
               << "local dominates return: "
               << dominance.dominates(adds[1].getResult(), ret) << "\n"
               << "if result dominates return: "
               << dominance.dominates(branch.getResult(0), ret) << "\n"
               << "base dead after if: "
               << liveness.isDeadAfter(adds[0].getResult(), branch) << "\n"
               << "if result dead after if: "
               << liveness.isDeadAfter(branch.getResult(0), branch) << "\n";
}

static void inspectAlias(ModuleOp module) {
  auto func = module.lookupSymbol<func::FuncOp>("memory");
  SmallVector<memref::AllocOp> allocations;
  SmallVector<memref::SubViewOp> views;
  memref::StoreOp store;
  func.walk([&](memref::AllocOp op) { allocations.push_back(op); });
  func.walk([&](memref::SubViewOp op) { views.push_back(op); });
  func.walk([&](memref::StoreOp op) { store = op; });
  AliasAnalysis aa(func);
  Value a = allocations[0], b = allocations[1];
  llvm::outs() << "arguments p/q: " << aa.alias(func.getArgument(0), func.getArgument(1))
               << "\nallocations a/b: " << aa.alias(a, b)
               << "\nsame value a/a: " << aa.alias(a, a)
               << "\nviews left/right: " << aa.alias(views[0], views[1])
               << "\nstore(a) vs a: " << aa.getModRef(store, a)
               << "\nstore(a) vs b: " << aa.getModRef(store, b) << "\n";
}

static LogicalResult inspectConstants(ModuleOp module) {
  DataFlowSolver solver;
  solver.load<dataflow::DeadCodeAnalysis>();
  solver.load<dataflow::SparseConstantPropagation>();
  if (failed(solver.initializeAndRun(module)))
    return failure();
  auto func = module.lookupSymbol<func::FuncOp>("propagate");
  SmallVector<arith::AddIOp> adds;
  scf::IfOp branch;
  func.walk([&](arith::AddIOp op) { adds.push_back(op); });
  func.walk([&](scf::IfOp op) { branch = op; });
  auto show = [&](StringRef name, Value value) {
    llvm::outs() << name << ": ";
    auto *state = solver.lookupState<dataflow::Lattice<dataflow::ConstantValue>>(value);
    if (!state || state->getValue().isUninitialized())
      llvm::outs() << "uninitialized";
    else if (Attribute attr = state->getValue().getConstantValue())
      llvm::outs() << attr;
    else
      llvm::outs() << "unknown";
    llvm::outs() << "\n";
  };
  show("sum", adds[0].getResult());
  show("if result", branch.getResult(0));
  show("out", adds[1].getResult());
  return success();
}

static LogicalResult inspectRanges(ModuleOp module) {
  DataFlowSolver solver;
  solver.load<dataflow::DeadCodeAnalysis>();
  solver.load<dataflow::SparseConstantPropagation>();
  solver.load<dataflow::IntegerRangeAnalysis>();
  if (failed(solver.initializeAndRun(module)))
    return failure();
  scf::ForOp loop;
  arith::AddIOp add;
  module.walk([&](scf::ForOp op) { loop = op; });
  module.walk([&](arith::AddIOp op) { add = op; });
  auto show = [&](StringRef name, Value value) {
    auto *state = solver.lookupState<dataflow::IntegerValueRangeLattice>(value);
    llvm::outs() << name << ": ";
    if (!state || state->getValue().isUninitialized())
      llvm::outs() << "uninitialized\n";
    else {
      const auto &range = state->getValue().getValue();
      llvm::outs() << range.smin() << ".." << range.smax() << "\n";
    }
  };
  show("i", loop.getInductionVar());
  show("next", add.getResult());
  return success();
}

int main(int argc, char **argv) {
  if (argc != 3) {
    llvm::errs() << "usage: inspect-analysis dominance|cfg|alias|constants|ranges|cache|stale|calls input.mlir\n";
    return 2;
  }
  DialectRegistry registry;
  registry.insert<arith::ArithDialect, func::FuncDialect, scf::SCFDialect,
                  cf::ControlFlowDialect, memref::MemRefDialect>();
  MLIRContext context(registry);
  context.disableMultithreading();
  auto module = parseSourceFile<ModuleOp>(argv[2], &context);
  if (!module || failed(verify(*module)))
    return 1;
  std::string mode = argv[1];
  if (mode == "dominance")
    inspectDominance(*module);
  else if (mode == "alias")
    inspectAlias(*module);
  else if (mode == "constants")
    return failed(inspectConstants(*module));
  else if (mode == "ranges")
    return failed(inspectRanges(*module));
  else if (mode == "cfg") {
    auto func = module->lookupSymbol<func::FuncOp>("diamond");
    SmallVector<Block *> blocks;
    for (Block &block : func.getBody()) blocks.push_back(&block);
    DominanceInfo dom(func);
    PostDominanceInfo post(func);
    llvm::outs() << "entry dominates join: " << dom.dominates(blocks[0], blocks[3])
                 << "\nthen dominates join: " << dom.dominates(blocks[1], blocks[3])
                 << "\njoin postdominates then: " << post.postDominates(blocks[3], blocks[1])
                 << "\nthen postdominates entry: " << post.postDominates(blocks[1], blocks[0]) << "\n";
  }
  else if (mode == "calls") {
    CallGraph graph(*module);
    graph.print(llvm::outs());
  } else if (mode == "cache" || mode == "stale") {
    PassManager pm(&context);
    pm.addNestedPass<func::FuncOp>(std::make_unique<ReportCount>());
    pm.addNestedPass<func::FuncOp>(std::make_unique<ReportCount>());
    pm.addNestedPass<func::FuncOp>(std::make_unique<AddConstant>(mode == "stale"));
    pm.addNestedPass<func::FuncOp>(std::make_unique<ReportCount>());
    return failed(pm.run(*module));
  } else {
    llvm::errs() << "unknown mode: " << mode << "\n";
    return 2;
  }
  return 0;
}
