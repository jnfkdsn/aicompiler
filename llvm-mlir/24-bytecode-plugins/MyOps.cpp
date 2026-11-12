#include "MyOps.h"
#include "mlir/Bytecode/BytecodeImplementation.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/DialectImplementation.h"
#include "llvm/Support/MathExtras.h"
using namespace mlir;
#include "MyDialect.cpp.inc"
#define GET_OP_CLASSES
#include "MyOps.cpp.inc"
namespace {
struct MyVersion : DialectVersion { uint64_t major=0; };
struct MyBytecode : BytecodeDialectInterface {
 explicit MyBytecode(Dialect *dialect) : BytecodeDialectInterface(dialect) {}
 void writeVersion(DialectBytecodeWriter &writer) const override {
  writer.writeVarInt(MY_DIALECT_VERSION);
 }
 std::unique_ptr<DialectVersion> readVersion(DialectBytecodeReader &reader) const override {
  auto version=std::make_unique<MyVersion>();
  if(failed(reader.readVarInt(version->major)))return nullptr;
  return version;
 }
 LogicalResult upgradeFromVersion(Operation *top,const DialectVersion &base) const override {
  auto old=static_cast<const MyVersion&>(base).major;
  if(old==0 || old>MY_DIALECT_VERSION)
   return top->emitError("unsupported my dialect version ")<<old<<" by reader "<<MY_DIALECT_VERSION;
#if MY_DIALECT_VERSION == 2
  if(old==1){
   bool invalid=false;
   top->walk([&](my::ShiftOp op){
    auto bias=op.getBiasAttr();
    if(!bias || op.getOffsetAttr()){
     op.emitError("invalid version 1 shift fields");invalid=true;return;
    }
    op->setAttr("offset",bias);op->removeAttr("bias");
   });
   if(invalid)return failure();
  }
#endif
  return success();
 }
};
}
void mlir::my::MyDialect::initialize(){
 addOperations<
#define GET_OP_LIST
#include "MyOps.cpp.inc"
 >();
 addInterfaces<MyBytecode>();
}
LogicalResult mlir::my::ShiftOp::verify(){
#if MY_DIALECT_VERSION == 1
 auto value=getBiasAttr();
 if(!value || getOffsetAttr())return emitOpError("version 1 requires only bias");
#else
 auto value=getOffsetAttr();
 if(!value || getBiasAttr())return emitOpError("version 2 requires only offset");
#endif
 if(!llvm::isInt<32>(value.getInt()))return emitOpError("offset must fit signed i32");
 return success();
}
