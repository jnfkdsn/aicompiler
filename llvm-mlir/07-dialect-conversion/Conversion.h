#ifndef MY_CLAMP_CONVERSION_H
#define MY_CLAMP_CONVERSION_H
#include "mlir/Transforms/DialectConversion.h"
void configureClampTarget(mlir::ConversionTarget &target);
void populateClampPatterns(mlir::RewritePatternSet &patterns);
void registerClampConversionPass();
#endif
