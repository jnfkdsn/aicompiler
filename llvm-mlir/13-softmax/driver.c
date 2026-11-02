#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  float *allocated, *aligned;
  int64_t offset, sizes[2], strides[2];
} MemRef2;
extern void _mlir_ciface_softmax(MemRef2 *, MemRef2 *);
extern void _mlir_ciface_row_softmax(MemRef2 *, MemRef2 *);
extern float _mlir_ciface_exp_value(float);
extern float _mlir_ciface_exp_minus_one(float);
extern float _mlir_ciface_accurate_small_exp(float);
extern float _mlir_ciface_llvm_accurate_small_exp(float);
extern uint64_t _mlir_ciface_tiles(uint64_t, uint64_t);
extern uint64_t _mlir_ciface_width_sensitive(void);
static int failed;

static MemRef2 descriptor(float *p, int64_t m, int64_t n) {
  MemRef2 d = {p,p,0,{m,n},{n,1}};
  return d;
}
static float read_element(MemRef2 d, int64_t i, int64_t j) {
  return d.aligned[d.offset+i*d.strides[0]+j*d.strides[1]];
}
static void test_softmax(const char *name, int64_t m, int64_t n, int pattern) {
  size_t count = (size_t)m*(size_t)n;
  float *input = malloc((count+2)*sizeof(float));
  float *scratch = malloc((count+2)*sizeof(float));
  float *saved = malloc((count ? count : 1)*sizeof(float));
  if (!input || !scratch || !saved) exit(2);
  input[0]=input[count+1]=54321.0f;
  scratch[0]=scratch[count+1]=12345.0f;
  for(size_t k=0;k<count;++k) {
    float v = (float)((int)(k%23)-11)*0.17f;
    if(pattern==1) v=1000.0f+(float)(k%n);
    if(pattern==2) v=-1000.0f+(float)(k%n);
    if(pattern==3) v=4.0f;
    if(pattern==4) v=(k%3==0 ? -1000.0f : (k%3==1 ? 0.0f : 1000.0f));
    if(pattern==5) v=(float)(k%n)+1.0f;
    input[k+1]=v; scratch[k+1]=-123.0f;
  }
  memcpy(saved,input+1,count*sizeof(float));
  MemRef2 in=descriptor(input+1,m,n), row=descriptor(scratch+1,m,n), baseline;
  _mlir_ciface_softmax(&baseline,&in);
  _mlir_ciface_row_softmax(&in,&row);
  int ok = baseline.sizes[0]==m && baseline.sizes[1]==n
        && scratch[0]==12345.0f && scratch[count+1]==12345.0f
        && input[0]==54321.0f && input[count+1]==54321.0f
        && memcmp(saved,input+1,count*sizeof(float))==0;
  int suite_ok[2]={1,1};
  double max_abs[2]={0,0}, max_rel[2]={0,0}, max_sum[2]={0,0}, max_pair=0;
  for(int64_t i=0;i<m && n>0;++i) {
    double max=-INFINITY, denom=0;
    for(int64_t j=0;j<n;++j) max=fmax(max,(double)input[1+i*n+j]);
    for(int64_t j=0;j<n;++j) denom+=exp((double)input[1+i*n+j]-max);
    double row_sums[2]={0,0};
    for(int64_t j=0;j<n;++j) {
      double ref=exp((double)input[1+i*n+j]-max)/denom;
      double actual[2]={read_element(baseline,i,j),read_element(row,i,j)};
      for(int s=0;s<2;++s) {
        double error=fabs(actual[s]-ref);
        max_abs[s]=fmax(max_abs[s],error);
        max_rel[s]=fmax(max_rel[s],error/fmax(fabs(ref),1e-30));
        row_sums[s]+=actual[s];
        suite_ok[s] &= isfinite(actual[s]) && actual[s]>=0 && error<=2e-6+2e-5*fabs(ref);
      }
      max_pair=fmax(max_pair,fabs(actual[0]-actual[1]));
      if(pattern==5 && i==0)
        printf("value\t%s\t%ld\t%.9g\t%.9g\t%.17g\n",name,(long)j,actual[0],actual[1],ref);
    }
    for(int s=0;s<2;++s) {
      max_sum[s]=fmax(max_sum[s],fabs(row_sums[s]-1));
      suite_ok[s] &= fabs(row_sums[s]-1)<=5e-5;
    }
  }
  for(int s=0;s<2;++s)
    printf("softmax\t%s\t%s\t%ld\t%ld\t%.9g\t%.9g\t%.9g\t%d\n",
        name,s==0?"tensor":"row",(long)m,(long)n,max_abs[s],max_rel[s],max_sum[s],ok && suite_ok[s]);
  printf("pair\t%s\t%.9g\t%d\n",name,max_pair,max_pair<=4e-6);
  failed += !ok || !suite_ok[0] || !suite_ok[1] || max_pair>4e-6;
  free(baseline.allocated); free(input); free(scratch); free(saved);
}

static void scalar(const char *name, double actual, double expected, double tol) {
  int ok=isfinite(actual) && fabs(actual-expected)<=tol;
  printf("scalar\t%s\t%.17g\t%.17g\t%d\n",name,actual,expected,ok);
  failed += !ok;
}
static void integer(const char *name, uint64_t actual, uint64_t expected) {
  int ok=actual==expected;
  printf("scalar\t%s\t%llu\t%llu\t%d\n",name,
      (unsigned long long)actual,(unsigned long long)expected,ok);
  failed += !ok;
}
int main(void) {
  _Static_assert(sizeof(void*)==8,"The C descriptor uses a 64-bit host ABI");
  test_softmax("two-by-three",2,3,5);
  test_softmax("shift-positive",2,3,1);
  test_softmax("shift-negative",2,3,2);
  test_softmax("uniform",3,7,3);
  test_softmax("underflow",2,3,4);
  test_softmax("single-column",4,1,0);
  test_softmax("odd-width",2,17,0);
  test_softmax("long-row",2,513,0);
  test_softmax("empty-batch",0,3,0);
  test_softmax("empty-row-extension",2,0,0);
  scalar("exp-zero",_mlir_ciface_exp_value(0),1,1e-7);
  scalar("exp-negative-one",_mlir_ciface_exp_value(-1),exp(-1),1e-7);
  scalar("exp-one",_mlir_ciface_exp_value(1),exp(1),3e-7);
  float tiny=1e-8f;
  double naive=_mlir_ciface_exp_minus_one(tiny);
  double careful=_mlir_ciface_accurate_small_exp(tiny);
  double llvm=_mlir_ciface_llvm_accurate_small_exp(tiny);
  scalar("exp-sub-tiny",naive,0,0);
  scalar("libm-expm1-tiny",careful,expm1((double)tiny),1e-14);
  scalar("llvm-expm1-tiny",llvm,0,0);
  integer("tiles-zero",_mlir_ciface_tiles(0,4),0);
  integer("tiles-ten",_mlir_ciface_tiles(10,4),3);
  integer("tiles-exact",_mlir_ciface_tiles(12,4),3);
  integer("tiles-wide",_mlir_ciface_tiles(UINT64_MAX,2),UINT64_C(9223372036854775808));
  integer("index64-division",_mlir_ciface_width_sensitive(),UINT64_C(2147483649));
  return failed != 0;
}
