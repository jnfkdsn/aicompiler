#include "mlir/IR/IRMapping.h"
#include "mlir/IR/SymbolTable.h"
#include "mlir/IR/Verifier.h"
#include "mlir/IR/Builders.h"
#include "mlir/Parser/Parser.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/ControlFlow/IR/ControlFlowOps.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/MemRef/IR/MemRef.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/Interfaces/SideEffectInterfaces.h"
#include "llvm/Support/raw_ostream.h"
using namespace mlir;
namespace {
struct CounterResource : SideEffects::Resource::Base<CounterResource>{
 MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(CounterResource)
 StringRef getName()override{return "TeachingCounter";}
};
}
int main(int argc,char **argv){
 if(argc!=2)return 2;
 MLIRContext ctx;ctx.loadDialect<arith::ArithDialect,cf::ControlFlowDialect,func::FuncDialect,memref::MemRefDialect,scf::SCFDialect>();
 auto module=parseSourceFile<ModuleOp>(argv[1],&ctx);if(!module)return 1;
 auto helper=module->lookupSymbol<func::FuncOp>("helper");
 SymbolTable table(*module);
 if(failed(table.rename(helper,"renamed")))return 1;
 llvm::outs()<<"renamed call: ";module->lookupSymbol<func::FuncOp>("caller").walk([](func::CallOp op){llvm::outs()<<op.getCallee()<<"\n";});
 IRMapping mapping;
 auto clone=cast<func::FuncOp>(helper->clone(mapping));clone.setName("helper_copy");table.insert(clone);
 llvm::outs()<<"clone blocks="<<clone.getBody().getBlocks().size()<<"\n";
 bool mapped=true;
 for(Block &block:helper.getBody()){
  mapped &= mapping.lookup(&block)!=&block && mapping.lookup(&block)->getParent()==&clone.getBody();
  for(BlockArgument arg:block.getArguments())mapped &= mapping.lookup(arg)!=arg;
 }
 auto branch=cast<cf::CondBranchOp>(clone.front().getTerminator());
 mapped &= branch.getTrueDest()->getParent()==&clone.getBody();
 mapped &= branch.getFalseDest()->getParent()==&clone.getBody();
 llvm::outs()<<"clone values and CFG remapped="<<mapped<<"\n";
 clone.walk([&](arith::AddIOp op){llvm::outs()<<"nested capture remapped="<<(op.getLhs()==clone.getArgument(1))<<"\n";});
 clone.walk([](func::CallOp op){llvm::outs()<<"clone symbol reference still="<<op.getCallee()<<"\n";});
 if(!mapped || failed(verify(*module)))return 1;
 // Move a constant required in both branches into just the true branch.
 auto c=cast<arith::ConstantOp>(&helper.front().front());
 auto originalTerm=helper.front().getTerminator();
 auto destination=cast<cf::CondBranchOp>(originalTerm).getTrueDest();
 c->moveBefore(&destination->front());
 bool rejected=failed(verify(*module));llvm::outs()<<"bad move rejected="<<rejected<<"\n";
 c->moveBefore(originalTerm);if(!rejected || failed(verify(*module)))return 1;
 llvm::outs()<<"repair verifies=1\n";
 module->walk([](Operation *op){
  if(!isa<memref::CopyOp,memref::AllocaOp>(op))return;
  SmallVector<MemoryEffects::EffectInstance> effects;
  cast<MemoryEffectOpInterface>(op).getEffects(effects);
  for(auto &e:effects){
   StringRef kind=isa<MemoryEffects::Read>(e.getEffect())?"read":isa<MemoryEffects::Write>(e.getEffect())?"write":"allocate";
   llvm::outs()<<op->getName()<<" "<<kind<<" resource="<<e.getResource()->getName()<<" stage="<<e.getStage()<<" full="<<e.getEffectOnFullRegion()<<"\n";
  }
 });
 // Protocol examples, not the effects declared by memref.copy above.
 MemoryEffects::EffectInstance stagedRead(MemoryEffects::Read::get(),0,true);
 MemoryEffects::EffectInstance stagedWrite(MemoryEffects::Write::get(),1,true);
 MemoryEffects::EffectInstance counterWrite(MemoryEffects::Write::get(),CounterResource::get());
 llvm::outs()<<"synthetic protocol read-stage="<<stagedRead.getStage()<<" write-stage="<<stagedWrite.getStage()<<" resource="<<counterWrite.getResource()->getName()<<"\n";
 // Unknown region op may define a symbol table; traversal must be conservative.
 ctx.allowUnregisteredDialects();
 auto opaque=parseSourceString<ModuleOp>(R"(module {
  func.func private @h() { return }
  "my.opaque"() ({ ^bb0: "my.end"() : ()->() }) : ()->()
 })",&ctx);
 if(!opaque)return 1;
 auto uses=SymbolTable::getSymbolUses(&opaque->getBodyRegion());
 llvm::outs()<<"unknown symbol uses known="<<bool(uses)<<"\n";
 SymbolTable opaqueTable(*opaque);auto h=opaque->lookupSymbol<func::FuncOp>("h");
 bool refused=!uses; // Application policy: do not rename with unknown use scope.
 if(!refused)refused=failed(opaqueTable.rename(h,"new_h"));
 llvm::outs()<<"guarded rename refused="<<refused<<" name-preserved="<<(h.getSymName()=="h")<<"\n";
 if(!refused || h.getSymName()!="h")return 1;
 llvm::outs()<<"final module:\n";module->print(llvm::outs());llvm::outs()<<"\n";
}
