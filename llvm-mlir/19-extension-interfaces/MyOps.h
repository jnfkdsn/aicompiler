#ifndef MY_EXTENSION_OPS_H
#define MY_EXTENSION_OPS_H
#include "mlir/Bytecode/BytecodeOpInterface.h"
#include "mlir/IR/BuiltinTypes.h"
#include "mlir/IR/Dialect.h"
#include "mlir/IR/OpDefinition.h"
#include "mlir/Interfaces/InferTypeOpInterface.h"
#include "mlir/Interfaces/ControlFlowInterfaces.h"
#include "mlir/Interfaces/SideEffectInterfaces.h"
#include "MyDialect.h.inc"
#define GET_OP_CLASSES
#include "MyOps.h.inc"
void registerMyBufferization(mlir::DialectRegistry &registry);
#endif
