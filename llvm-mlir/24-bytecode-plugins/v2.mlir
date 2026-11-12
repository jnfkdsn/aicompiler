module {
 func.func @answer()->i32 {
  %x=arith.constant 37:i32
  %y=my.shift %x {offset=5:i64}:i32
  return %y:i32
 }
}
