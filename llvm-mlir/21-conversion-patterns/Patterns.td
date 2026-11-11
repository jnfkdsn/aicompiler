include "mlir/IR/PatternBase.td"
include "MyOps.td"
def IsZero : Constraint<CPred<"::mlir::matchPattern($0, ::mlir::m_Zero())">>;
def RemoveRightZero : Pat<(AddOp $x, $zero), (replaceWithValue $x), [(IsZero $zero)]>;
