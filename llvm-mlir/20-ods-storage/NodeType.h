#ifndef MY_NODE_TYPE_H
#define MY_NODE_TYPE_H
#include "mlir/IR/Types.h"
#include "mlir/Support/TypeID.h"
// Programmatic-only nominal type, demonstrating the same staged construction
// principle as LLVM's TestRecursiveType. It has no text or lowering contract.
namespace mlir::my {
struct NodeStorage : TypeStorage {
  using KeyTy=StringRef;
  explicit NodeStorage(StringRef name):name(name){}
  bool operator==(const KeyTy &key) const {return name==key;}
  static NodeStorage *construct(TypeStorageAllocator &allocator, const KeyTy &key) {
    return new(allocator.allocate<NodeStorage>()) NodeStorage(allocator.copyInto(key));
  }
  LogicalResult mutate(TypeStorageAllocator &,Type proposed) {
    if(body && body!=proposed)return failure();
    body=proposed;return success();
  }
  StringRef name;
  Type body;
};
class NodeType : public Type::TypeBase<NodeType,Type,NodeStorage,TypeTrait::IsMutable> {
public:
  using Base::Base;
  static constexpr StringLiteral name="my.node";
  static NodeType get(MLIRContext *ctx,StringRef key){return Base::get(ctx,key);}
  LogicalResult setBody(Type body){return Base::mutate(body);}
  Type getBody() const{return getImpl()->body;}
  StringRef getName() const{return getImpl()->name;}
};
}
#endif
