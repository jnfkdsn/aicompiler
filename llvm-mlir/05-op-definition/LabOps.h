#ifndef LAB_OPS_H
#define LAB_OPS_H
#include "mlir/Bytecode/BytecodeOpInterface.h"
#include "mlir/IR/BuiltinTypes.h"
#include "mlir/IR/Dialect.h"
#include "mlir/IR/OpDefinition.h"
#include "mlir/Interfaces/SideEffectInterfaces.h"
#include "LabDialect.h.inc"
#define GET_OP_CLASSES
#include "LabOps.h.inc"
#endif
