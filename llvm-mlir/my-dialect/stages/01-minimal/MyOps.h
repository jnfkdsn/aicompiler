#ifndef MY_OPS_H
#define MY_OPS_H
#include "mlir/IR/BuiltinTypes.h"
#include "mlir/IR/Dialect.h"
#include "mlir/IR/OpDefinition.h"
#include "MyDialect.h.inc"
#define GET_OP_CLASSES
#include "MyOps.h.inc"
#endif
