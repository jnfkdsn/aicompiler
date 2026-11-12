#include "MyOps.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/Builders.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Tools/Plugins/DialectPlugin.h"
#include "mlir/Tools/Plugins/PassPlugin.h"
#include "llvm/Config/llvm-config.h"
using namespace mlir;
namespace {
struct Mark : PassWrapper<Mark,OperationPass<ModuleOp>> {
 MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(Mark)
 StringRef getArgument()const final{return "my-plugin-mark";}
 StringRef getDescription()const final{return "Attach a visible plugin marker";}
 void runOnOperation()override{
  getOperation()->setAttr("my.plugin_seen",UnitAttr::get(&getContext()));
 }
};
}
extern "C" LLVM_ATTRIBUTE_WEAK PassPluginLibraryInfo mlirGetPassPluginInfo(){
 return {MLIR_PLUGIN_API_VERSION,"MyPass",LLVM_VERSION_STRING,[](){PassRegistration<Mark>();}};
}
extern "C" LLVM_ATTRIBUTE_WEAK DialectPluginLibraryInfo mlirGetDialectPluginInfo(){
 return {MLIR_PLUGIN_API_VERSION,"MyDialect",LLVM_VERSION_STRING,[](DialectRegistry *r){r->insert<my::MyDialect>();}};
}
