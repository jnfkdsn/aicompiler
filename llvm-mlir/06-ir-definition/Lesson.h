#ifndef LESSON_H
#define LESSON_H
#include "mlir/Bytecode/BytecodeOpInterface.h"
#include "mlir/IR/BuiltinTypes.h"
#include "mlir/IR/Dialect.h"
#include "mlir/IR/OpDefinition.h"
#include "mlir/Interfaces/SideEffectInterfaces.h"
#include "LessonDialect.h.inc"
#define GET_TYPEDEF_CLASSES
#include "LessonTypes.h.inc"
#define GET_ATTRDEF_CLASSES
#include "LessonAttrs.h.inc"
#include "LessonInterfaces.h.inc"
#define GET_OP_CLASSES
#include "LessonOps.h.inc"
#endif
