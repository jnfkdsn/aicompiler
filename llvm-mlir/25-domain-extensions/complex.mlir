module {
 func.func @multiply(%a:complex<f32>,%b:complex<f32>)->complex<f32>{
  %r=complex.mul %a,%b:complex<f32>
  return %r:complex<f32>
 }
 func.func @norm(%a:complex<f32>)->f32{
  %r=complex.abs %a:complex<f32>
  return %r:f32
 }
 func.func @example()->(f32,f32){
  %one=arith.constant 1.0:f32
  %two=arith.constant 2.0:f32
  %three=arith.constant 3.0:f32
  %four=arith.constant 4.0:f32
  %a=complex.create %one,%two:complex<f32>
  %b=complex.create %three,%four:complex<f32>
  %p=complex.mul %a,%b:complex<f32>
  %re=complex.re %p:complex<f32>
  %im=complex.im %p:complex<f32>
  return %re,%im:f32,f32
 }
}
