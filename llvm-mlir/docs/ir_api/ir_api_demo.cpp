// Compiler-side examples for blog/compiler/ir_api.md, LLVM 20.1.8.
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/IRMapping.h"
#include "mlir/IR/Verifier.h"
#include "mlir/Interfaces/SideEffectInterfaces.h"
#include "mlir/Parser/Parser.h"
#include "llvm/ADT/SmallPtrSet.h"
#include "llvm/ADT/SmallVector.h"
#include "llvm/Support/raw_ostream.h"

using namespace mlir;

static void inspect(func::FuncOp fn) {
  // BEGIN: inspect
  Region &body = fn.getBody();
  Block &entry = body.front();
  Value x = entry.getArgument(0);
  llvm::errs() << "argument_has_defining_op="
               << (x.getDefiningOp() != nullptr) << "\n";
  fn.walk([](arith::AddIOp add) {
    Operation *raw = add.getOperation();
    Value lhs = add.getLhs();
    Value result = add.getResult();
    llvm::errs() << raw->getName() << " lhs_type=" << lhs.getType()
                 << " result_uses=" << std::distance(result.use_begin(),
                                                     result.use_end()) << "\n";
  });
  unsigned uses = 0;
  llvm::SmallPtrSet<Operation *, 4> uniqueUsers;
  for (OpOperand &use : x.getUses()) {
    ++uses;
    uniqueUsers.insert(use.getOwner());
    llvm::errs() << "x operand_slot=" << use.getOperandNumber() << "\n";
  }
  llvm::errs() << "x_uses=" << uses << " x_unique_users="
               << uniqueUsers.size() << "\n";
  // END: inspect
}

static void removeAddZero(func::FuncOp fn) {
  // BEGIN: remove-zero
  llvm::SmallVector<arith::AddIOp> candidates;
  fn.walk([&](arith::AddIOp add) { candidates.push_back(add); });
  for (arith::AddIOp add : candidates) {
    if (!add.getType().isSignlessInteger(32) ||
        add.getOverflowFlags() != arith::IntegerOverflowFlags::none)
      continue;
    auto constant = add.getRhs().getDefiningOp<arith::ConstantOp>();
    if (!constant)
      continue;
    auto integer = dyn_cast<IntegerAttr>(constant.getValue());
    if (!integer || !integer.getValue().isZero())
      continue;
    Value oldValue = add.getResult();
    Value replacement = add.getLhs();
    oldValue.replaceAllUsesWith(replacement);
    add.erase();
  }
  // END: remove-zero
}

static void multiplyTwice(func::FuncOp fn, bool badDominance) {
  // BEGIN: multiply
  OpBuilder builder(fn.getContext());
  llvm::SmallVector<arith::AddIOp> candidates;
  fn.walk([&](arith::AddIOp add) { candidates.push_back(add); });
  for (arith::AddIOp add : candidates) {
    if (!add.getType().isSignlessInteger(32) ||
        add.getOverflowFlags() != arith::IntegerOverflowFlags::none ||
        add.getLhs() != add.getRhs())
      continue;
    OpBuilder::InsertionGuard guard(builder);
    builder.setInsertionPoint(add);
    if (badDominance)
      builder.setInsertionPointAfter(add); // Deliberate verifier counterexample.
    Location loc = add.getLoc();
    auto two = builder.create<arith::ConstantIntOp>(loc, 2, 32);
    builder.setInsertionPoint(add);
    auto mul = builder.create<arith::MulIOp>(loc, add.getLhs(), two.getResult());
    add.getResult().replaceAllUsesWith(mul.getResult());
    add.erase();
  }
  // END: multiply
}

static void removeUnusedConstants(func::FuncOp fn) {
  // BEGIN: cleanup
  Block &entry = fn.getBody().front();
  for (Operation &op : llvm::make_early_inc_range(entry)) {
    if (isa<arith::ConstantOp>(op) && isOpTriviallyDead(&op))
      op.erase();
  }
  // END: cleanup
}

static void buildFunction(ModuleOp module) {
  // BEGIN: build
  OpBuilder builder(module.getContext());
  OpBuilder::InsertionGuard guard(builder);
  builder.setInsertionPointToEnd(module.getBody());
  Type i32 = builder.getI32Type();
  auto type = builder.getFunctionType({i32}, {i32});
  Location loc = builder.getUnknownLoc();
  auto fn = builder.create<func::FuncOp>(loc, "twice_built", type);
  Block *entry = fn.addEntryBlock();
  builder.setInsertionPointToStart(entry);
  Value x = entry->getArgument(0);
  auto sum = builder.create<arith::AddIOp>(loc, x, x);
  builder.create<func::ReturnOp>(loc, sum.getResult());
  // END: build
}

static void cloneFunctionBody(ModuleOp module, func::FuncOp source,
                              bool omitArgumentMapping) {
  // BEGIN: clone
  OpBuilder builder(module.getContext());
  OpBuilder::InsertionGuard guard(builder);
  builder.setInsertionPointToEnd(module.getBody());
  auto copy = builder.create<func::FuncOp>(source.getLoc(), "twice_copy",
                                          source.getFunctionType());
  Block *target = copy.addEntryBlock();
  IRMapping mapping;
  if (!omitArgumentMapping)
    mapping.map(source.getArguments(), target->getArguments());
  builder.setInsertionPointToStart(target);
  for (Operation &op : source.getBody().front())
    builder.clone(op, mapping);
  // END: clone
}

// Teaching mode: expose the intermediate state that the normal rewrite
// deliberately does not print. Keep old handles unused after erase.
static LogicalResult traceFirstAddZero(ModuleOp module, func::FuncOp fn) {
  for (auto add : fn.getBody().front().getOps<arith::AddIOp>()) {
    if (!add.getType().isSignlessInteger(32) ||
        add.getOverflowFlags() != arith::IntegerOverflowFlags::none)
      continue;
    auto constant = add.getRhs().getDefiningOp<arith::ConstantOp>();
    auto integer = constant ? dyn_cast<IntegerAttr>(constant.getValue())
                            : IntegerAttr();
    if (!integer || !integer.getValue().isZero())
      continue;
    Value oldValue = add.getResult();
    Value replacement = add.getLhs();
    auto show = [&](StringRef label, bool oldAlive) {
      llvm::errs() << "\n[" << label << "]\n";
      if (oldAlive)
        llvm::errs() << "old_uses=" << std::distance(oldValue.use_begin(),
                                                   oldValue.use_end()) << "\n";
      else
        llvm::errs() << "old operation erased; old handles are no longer accessed\n";
      llvm::errs() << "replacement_uses="
                   << std::distance(replacement.use_begin(), replacement.use_end())
                   << "\n";
      for (OpOperand &use : replacement.getUses())
        llvm::errs() << "  replacement -> " << use.getOwner()->getName()
                     << " operand " << use.getOperandNumber() << "\n";
      module.print(llvm::errs());
      llvm::errs() << "\n";
    };
    show("before", true);
    oldValue.replaceAllUsesWith(replacement);
    show("after-rauw: old operation still exists", true);
    if (failed(verify(module)))
      return failure();
    add.erase();
    show("after-erase", false);
    return success(); // Do not increment an iterator whose current op was erased.
  }
  llvm::errs() << "No matching unflagged i32 add with a constant zero RHS\n";
  return failure();
}

int main(int argc, char **argv) {
  if (argc != 3) {
    llvm::errs() << "usage: ir-api-demo MODE input.mlir\n";
    return 1;
  }
  StringRef mode(argv[1]);
  if (mode != "inspect" && mode != "zero" && mode != "rewrite" &&
      mode != "bad-dominance" && mode != "build" && mode != "clone" &&
      mode != "bad-clone" && mode != "trace-one") {
    llvm::errs() << "unknown mode\n";
    return 1;
  }
  // BEGIN: parse
  DialectRegistry registry;
  registry.insert<arith::ArithDialect, func::FuncDialect>();
  MLIRContext context(registry);
  context.loadDialect<arith::ArithDialect, func::FuncDialect>();
  OwningOpRef<ModuleOp> module = parseSourceFile<ModuleOp>(argv[2], &context);
  if (!module || failed(verify(module->getOperation())))
    return 1;
  // END: parse
  auto fn = module->lookupSymbol<func::FuncOp>("twice");
  if (!fn || fn.isExternal() || !llvm::hasSingleElement(fn.getBody()) ||
      fn.getNumArguments() != 1 || fn.getFunctionType().getNumResults() != 1 ||
      !fn.getArgument(0).getType().isSignlessInteger(32) ||
      !fn.getFunctionType().getResult(0).isSignlessInteger(32) ||
      module->lookupSymbol("twice_built") || module->lookupSymbol("twice_copy")) {
    llvm::errs() << "expected single-block @twice : (i32) -> i32 and free demo names\n";
    return 1;
  }
  if (mode == "inspect") {
    inspect(fn);
  } else if (mode == "trace-one") {
    if (failed(traceFirstAddZero(*module, fn)))
      return 2;
  } else if (mode == "build") {
    buildFunction(*module);
  } else if (mode == "clone" || mode == "bad-clone") {
    cloneFunctionBody(*module, fn, mode == "bad-clone");
  } else {
    removeAddZero(fn);
    if (failed(verify(module->getOperation())))
      return 2;
    if (mode != "zero") {
      multiplyTwice(fn, mode == "bad-dominance");
      removeUnusedConstants(fn);
    }
  }
  // BEGIN: verify
  if (failed(verify(module->getOperation()))) {
    llvm::errs() << "IR after failed verification:\n";
    module->print(llvm::errs());
    llvm::errs() << "\n";
    return 2;
  }
  module->print(llvm::outs());
  llvm::outs() << "\n";
  return 0;
  // END: verify
}
