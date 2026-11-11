#include "MyOps.h"
#include "NodeType.h"
#include "mlir/IR/MLIRContext.h"
#include "llvm/Support/raw_ostream.h"
#include <optional>
using namespace mlir;
// The consumer knows protocols, not the concrete TileType/AlignmentAttr classes.
static std::optional<std::pair<int64_t,int64_t>> plan(Type type, Attribute policy,
                                                     int64_t start,int64_t capacity) {
  auto info=dyn_cast<my::TileInfo>(type);
  auto alignment=dyn_cast<my::AlignmentPolicy>(policy);
  if(!info || !alignment || start<0 || capacity<start)return std::nullopt;
  int64_t a=alignment.getRequiredAlignment(),bytes=info.getPayloadBytes();
  if(a<=0 || bytes<0)return std::nullopt;
  int64_t padding=(a-start%a)%a;
  if(padding>capacity-start || bytes>capacity-start-padding)return std::nullopt;
  return std::pair<int64_t,int64_t>{start+padding,start+padding+bytes};
}
int main() {
  MLIRContext ctx;
  ctx.getOrLoadDialect<my::MyDialect>();
  SmallVector<int64_t> shape{2,3};
  auto tile=my::TileType::get(&ctx,shape);
  shape[0]=99;shape.clear();
  auto same=my::TileType::get(&ctx,ArrayRef<int64_t>{2,3});
  auto policy=my::AlignmentAttr::get(&ctx,16);
  auto info=cast<my::TileInfo>(tile);
  auto alignment=cast<my::AlignmentPolicy>(policy);
  int64_t bytes=info.getPayloadBytes(),a=alignment.getRequiredAlignment();
  int64_t start=5,padded=(start+a-1)/a*a,end=padded+bytes;
  llvm::outs()<<"tile="<<tile<<" same="<<(tile==same)<<" bytes="<<bytes
              <<" alignment="<<a<<" start="<<padded<<" end="<<end<<"\n";
  auto node=my::NodeType::get(&ctx,"Node");
  auto alias=my::NodeType::get(&ctx,"Node");
  Type body=TupleType::get(&ctx,{IntegerType::get(&ctx,32),node});
  bool first=succeeded(node.setBody(body)),repeat=succeeded(alias.setBody(body));
  bool conflict=failed(node.setBody(IntegerType::get(&ctx,64)));
  llvm::outs()<<"node="<<node.getName()<<" same="<<(node==alias)<<" first="<<first<<" repeat="<<repeat<<" conflict_rejected="<<conflict<<" shared_body="<<(alias.getBody()==body)<<"\n";
  auto good=plan(tile,policy,5,64);
  bool rejected=!plan(tile,policy,5,32) && !plan(IntegerType::get(&ctx,32),policy,5,64);
  llvm::outs()<<"planner capacity64="<<bool(good)<<" bounds_and_protocol_rejected="<<rejected<<"\n";
  bool nominal=bool(good) && good->first==16 && good->second==40 && rejected && first && repeat && conflict && node==alias && alias.getBody()==body;
  return nominal && tile==same && tile.getShape()[0]==2 && bytes==24 && padded==16 && end==40 ? 0:1;
}
