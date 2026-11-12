#include "mlir/Tools/Plugins/PassPlugin.h"
#include "llvm/Support/Error.h"
#include "llvm/Support/raw_ostream.h"
int main(int argc,char **argv){
 if(argc!=2)return 2;
 auto plugin=mlir::PassPlugin::load(argv[1]);
 if(!plugin){llvm::errs()<<llvm::toString(plugin.takeError())<<"\n";return 1;}
 llvm::outs()<<plugin->getPluginName()<<"\n";return 0;
}
