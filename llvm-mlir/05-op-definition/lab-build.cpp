#include "LabOps.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/Verifier.h"
#include "llvm/Support/raw_ostream.h"
using namespace mlir;
int main(int argc, char **argv) {
  bool invalid = argc == 2 && StringRef(argv[1]) == "invalid";
  if (argc > 2 || (argc == 2 && !invalid))
    return 2;
  MLIRContext context;
  context.loadDialect<lab::LabDialect, func::FuncDialect>();
  OpBuilder builder(&context);
  auto loc = builder.getUnknownLoc();
  OwningOpRef<ModuleOp> module = ModuleOp::create(loc);
  builder.setInsertionPointToEnd(module->getBody());
  auto fn = builder.create<func::FuncOp>(loc, "clip",
      builder.getFunctionType({builder.getI32Type()}, {builder.getI32Type()}));
  Block *entry = fn.addEntryBlock();
  builder.setInsertionPointToStart(entry);
  Value x = entry->getArgument(0);
  // BEGIN: builder
  auto clamp = builder.create<lab::ClampOp>(
      loc, builder.getI32Type(), x,
      builder.getI32IntegerAttr(invalid ? 8 : -4), builder.getI32IntegerAttr(7));
  builder.create<func::ReturnOp>(loc, clamp.getResult());
  // END: builder
  llvm::errs() << "builder completed; input_type=" << clamp.getInput().getType()
               << " lower=" << clamp.getLowerAttr().getInt()
               << " upper=" << clamp.getUpperAttr().getInt() << "\n";
  module->print(llvm::outs());
  llvm::outs() << "\n";
  return failed(verify(module->getOperation())) ? 1 : 0;
}
