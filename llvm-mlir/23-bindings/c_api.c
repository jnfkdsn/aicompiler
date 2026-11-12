#include "mlir-c/IR.h"
#include "mlir-c/BuiltinAttributes.h"
#include "mlir-c/BuiltinTypes.h"
#include "mlir-c/Dialect/Arith.h"
#include "mlir-c/Dialect/Func.h"
#include "mlir-c/Pass.h"
#include "mlir-c/Transforms.h"
#include <stdio.h>
#define STR(s) mlirStringRefCreateFromCString(s)
static void printChunk(MlirStringRef s,void *data){fwrite(s.data,1,s.length,(FILE*)data);}
int main(void) {
  int status=0;
  MlirContext ctx=mlirContextCreate();
  mlirDialectHandleRegisterDialect(mlirGetDialectHandle__arith__(),ctx);
  mlirDialectHandleRegisterDialect(mlirGetDialectHandle__func__(),ctx);
  mlirRegisterTransformsPasses();
  const char *source="module {func.func @answer()->i32 { %a=arith.constant 20:i32 %b=arith.constant 22:i32 %r=arith.addi %a,%b:i32 return %r:i32 }}";
  MlirModule module=mlirModuleCreateParse(ctx,STR(source));
  if(mlirModuleIsNull(module)){mlirContextDestroy(ctx);return 1;}
  MlirOperation top=mlirModuleGetOperation(module);
  MlirPassManager pm=mlirPassManagerCreate(ctx);
  MlirOpPassManager opm=mlirPassManagerGetAsOpPassManager(pm);
  if(mlirLogicalResultIsFailure(mlirParsePassPipeline(opm,STR("builtin.module(canonicalize)"),printChunk,stderr))){status=2;goto cleanup;}
  if(mlirLogicalResultIsFailure(mlirPassManagerRunOnOp(pm,top))){status=3;goto cleanup;}
  puts("after fold:");mlirOperationPrint(top,printChunk,stdout);puts("");
  // All the following handles borrow objects owned by the module/context.
  MlirOperation function=mlirBlockGetFirstOperation(mlirModuleGetBody(module));
  MlirBlock block=mlirRegionGetFirstBlock(mlirOperationGetRegion(function,0));
  MlirOperation ret=mlirBlockGetTerminator(block);
  MlirType i32=mlirIntegerTypeGet(ctx,32);
  MlirNamedAttribute value=mlirNamedAttributeGet(mlirIdentifierGet(ctx,STR("value")),mlirIntegerAttrGet(i32,7));
  MlirOperationState state=mlirOperationStateGet(STR("arith.constant"),mlirLocationUnknownGet(ctx));
  mlirOperationStateAddResults(&state,1,&i32);mlirOperationStateAddAttributes(&state,1,&value);
  MlirOperation seven=mlirOperationCreate(&state);
  if(mlirOperationIsNull(seven)){status=4;goto cleanup;}
  // Ownership transfers to the block; do not destroy seven separately.
  mlirBlockInsertOwnedOperationBefore(block,ret,seven);
  mlirOperationSetOperand(ret,0,mlirOperationGetResult(seven,0));
  if(!mlirOperationVerify(top)){status=5;goto cleanup;}
  if(mlirLogicalResultIsFailure(mlirPassManagerRunOnOp(pm,top))){status=6;goto cleanup;}
  puts("after replacement:");mlirOperationPrint(top,printChunk,stdout);puts("");
  // A transformation may invalidate borrowed op handles. Reacquire if needed.
cleanup:
  mlirPassManagerDestroy(pm);mlirModuleDestroy(module);mlirContextDestroy(ctx);
  return status;
}
