#include "mlir/Tools/Plugins/PassPlugin.h"
extern "C" LLVM_ATTRIBUTE_WEAK mlir::PassPluginLibraryInfo mlirGetPassPluginInfo(){
 return {MLIR_PLUGIN_API_VERSION+1,"DeliberatelyIncompatible","0",[](){}};
}
