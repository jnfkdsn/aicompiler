module {
 func.func @sum(%a:i32,%b:i32)->i32 {
  %r="my.add"(%a,%b):(i32,i32)->i32
  return %r:i32
 }
 func.func @unused(%a:i32,%b:i32) {
  %r="my.add"(%a,%b):(i32,i32)->i32
  return
 }
}
