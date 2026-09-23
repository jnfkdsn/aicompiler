// RUN: %lab-opt %s --split-input-file --verify-diagnostics
func.func @reversed(%x: i32) -> i32 {
 // expected-error @+1 {{requires lower <= upper (signed i32)}}
 %r = lab.clamp %x bounds(8, 7) : i32
 return %r : i32
}
// -----
func.func @wide_input(%x: i64) -> i32 {
 // expected-error @+1 {{operand #0 must be 32-bit signless integer}}
 %r = "lab.clamp"(%x) <{lower = -4 : i32, upper = 7 : i32}> : (i64) -> i32
 return %r : i32
}
// -----
func.func @wide_result(%x: i32) -> i64 {
 // expected-error @+1 {{result #0 must be 32-bit signless integer}}
 %r = "lab.clamp"(%x) <{lower = -4 : i32, upper = 7 : i32}> : (i32) -> i64
 return %r : i64
}
// -----
func.func @missing(%x: i32) -> i32 {
 // expected-error @+1 {{requires attribute 'lower'}}
 %r = "lab.clamp"(%x) <{upper = 7 : i32}> : (i32) -> i32
 return %r : i32
}
// -----
func.func @wide_bound(%x: i32) -> i32 {
 // expected-error @+1 {{attribute 'lower' failed to satisfy constraint}}
 %r = "lab.clamp"(%x) <{lower = -4 : i64, upper = 7 : i32}> : (i32) -> i32
 return %r : i32
}
// -----
func.func @extra_operand(%x: i32) -> i32 {
 // expected-error @+1 {{requires a single operand}}
 %r = "lab.clamp"(%x, %x) <{lower = -4 : i32, upper = 7 : i32}> : (i32, i32) -> i32
 return %r : i32
}
