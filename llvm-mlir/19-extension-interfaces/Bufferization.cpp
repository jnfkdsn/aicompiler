#include "MyOps.h"
#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Bufferization/IR/BufferizableOpInterface.h"
#include "mlir/Dialect/MemRef/IR/MemRef.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
using namespace mlir;
using namespace mlir::bufferization;
namespace {
struct AddOneModel : BufferizableOpInterface::ExternalModel<AddOneModel, my::AddOneOp> {
  bool bufferizesToMemoryRead(Operation *, OpOperand &operand,
                              const AnalysisState &) const {
    return operand.getOperandNumber() == 0;
  }
  bool bufferizesToMemoryWrite(Operation *, OpOperand &operand,
                               const AnalysisState &) const {
    return operand.getOperandNumber() == 1;
  }
  AliasingValueList getAliasingValues(Operation *op, OpOperand &operand,
                                     const AnalysisState &) const {
    if (operand.getOperandNumber() == 1)
      return {{op->getResult(0), BufferRelation::Equivalent}};
    return {};
  }
  bool bufferizesToElementwiseAccess(Operation *, const AnalysisState &,
                                     ArrayRef<OpOperand *>) const {
    return true;
  }
  LogicalResult bufferize(Operation *op, RewriterBase &rewriter,
                          const BufferizationOptions &options) const {
    auto add = cast<my::AddOneOp>(op);
    FailureOr<Value> input = getBuffer(rewriter, add.getInput(), options);
    FailureOr<Value> output = getBuffer(rewriter, add.getInit(), options);
    if (failed(input) || failed(output))
      return failure();
    OpBuilder::InsertionGuard guard(rewriter);
    rewriter.setInsertionPoint(op);
    Location loc = op->getLoc();
    Value zero = rewriter.create<arith::ConstantIndexOp>(loc, 0);
    Value one = rewriter.create<arith::ConstantIndexOp>(loc, 1);
    Value size = rewriter.create<memref::DimOp>(loc, *input, zero);
    Value increment = rewriter.create<arith::ConstantOp>(loc, rewriter.getF32FloatAttr(1.0));
    auto loop = rewriter.create<scf::ForOp>(loc, zero, size, one);
    rewriter.setInsertionPointToStart(loop.getBody());
    Value old = rewriter.create<memref::LoadOp>(loc, *input, loop.getInductionVar());
    Value next = rewriter.create<arith::AddFOp>(loc, old, increment);
    rewriter.create<memref::StoreOp>(loc, next, *output, loop.getInductionVar());
    rewriter.setInsertionPoint(op);
    replaceOpWithBufferizedValues(rewriter, op, *output);
    return success();
  }
};
} // namespace
void registerMyBufferization(DialectRegistry &registry) {
  registry.addExtension(+[](MLIRContext *ctx, my::MyDialect *) {
    ctx->getOrLoadDialect<arith::ArithDialect>();
    ctx->getOrLoadDialect<memref::MemRefDialect>();
    ctx->getOrLoadDialect<scf::SCFDialect>();
    my::AddOneOp::attachInterface<AddOneModel>(*ctx);
  });
}
