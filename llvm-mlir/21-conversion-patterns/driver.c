#include <stdint.h>
#include <stdio.h>
extern int32_t _mlir_ciface_entry(int32_t,int32_t);
extern int32_t _mlir_ciface_difference(int32_t,int32_t);
int main(void) {
  const int32_t cases[][2]={{20,22},{0,0},{-3,5},{100,-100}};
  int failed=0;
  for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
    int32_t a=cases[i][0],b=cases[i][1],actual=_mlir_ciface_entry(a,b),expected=a+b;
    int32_t difference=_mlir_ciface_difference(a,b);
    printf("%d + %d = %d expected %d; difference=%d expected %d\n",a,b,actual,expected,difference,a-b);
    failed+=(actual!=expected || difference!=a-b);
  }
  return failed?1:0;
}
