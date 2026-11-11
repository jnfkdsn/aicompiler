#include <stdint.h>
#include <stdio.h>
typedef struct { float *allocated, *aligned; int64_t offset, sizes[1], strides[1]; } M;
typedef struct { float old, updated; } Pair;
extern float _mlir_ciface_reuse(M *);
extern void _mlir_ciface_preserve(Pair *, M *);
int main(void) {
  const float starts[] = {10, -3, 0, 0.25f};
  int failed=0;
  for (int k=0; k<4; ++k) {
    float a[4],b[4];
    for(int i=0;i<4;++i) a[i]=b[i]=starts[k]+i;
    M ma={a,a,0,{4},{1}},mb={b,b,0,{4},{1}}; Pair p;
    float r=_mlir_ciface_reuse(&ma);
    _mlir_ciface_preserve(&p,&mb);
    int ok=r==starts[k]+1 && p.old==starts[k] && p.updated==starts[k]+1;
    for(int i=0;i<4;++i) ok=ok && a[i]==starts[k]+i+1 && b[i]==starts[k]+i;
    printf("case%d reuse=%g old=%g new=%g preserved=%d\n",k,r,p.old,p.updated,ok);
    failed+=!ok;
  }
  return failed ? 1 : 0;
}
