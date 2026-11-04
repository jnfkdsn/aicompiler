#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
typedef struct { float *allocated,*aligned; int64_t offset,sizes[1],strides[1]; } MemRef1;
typedef struct { float *allocated,*aligned; int64_t offset,sizes[2],strides[2]; } MemRef2;
#define DECL(name) extern void _mlir_ciface_##name(MemRef1*,MemRef1*)
DECL(scalar); DECL(automatic); DECL(transfer); DECL(masked); DECL(split);
extern void _mlir_ciface_values(MemRef2*,MemRef2*);
extern float _mlir_ciface_reduction(MemRef1*);
extern void _mlir_ciface_dot(MemRef2*,MemRef2*,MemRef2*);
static int failed;
static MemRef1 one(float*p,int64_t n){MemRef1 d={p,p,0,{n},{1}};return d;}
static MemRef2 two(float*p,int64_t m,int64_t n){MemRef2 d={p,p,0,{m,n},{n,1}};return d;}
static void report(const char *name,int count,int errors){printf("case\t%s\t%d\t%d\n",name,count,errors);failed+=errors!=0;}
int main(void){
  _Static_assert(sizeof(void*)==8,"64-bit ABI required");
  const char *names[]={"scalar","automatic","transfer","masked","split"};
  void(*f[])(MemRef1*,MemRef1*)={_mlir_ciface_scalar,_mlir_ciface_automatic,_mlir_ciface_transfer,_mlir_ciface_masked,_mlir_ciface_split};
  const int sizes[]={0,1,2,3,4,5,7,8,10,17,1025};
  for(int t=0;t<11;++t){
    int n=sizes[t];float *x=malloc((n+8)*sizeof(float)),*y=malloc((n+8)*sizeof(float));if(!x||!y)exit(2);
    for(int k=0;k<n+8;++k)x[k]=(float)(k-6);
    for(int v=0;v<5;++v){
      for(int k=0;k<n+8;++k)y[k]=-777;
      MemRef1 xd=one(x+4,n),yd=one(y+4,n);f[v](&xd,&yd);int errors=0;
      for(int k=0;k<n;++k)errors+=y[k+4]!=2*(x[k+4]+1);
      for(int k=0;k<4;++k)errors+=y[k]!=-777 || y[n+4+k]!=-777;
      for(int k=0;k<n+8;++k)errors+=x[k]!=(float)(k-6);
      char label[80];snprintf(label,sizeof(label),"%s-n%d",names[v],n);report(label,n,errors);
      if(n==10&&v==1)printf("sample\ttail\t%.0f\t%.0f\t%.0f\n",y[12],y[13],y[14]);
    }
    free(x);free(y);
  }
  float a[]={0,1,2,3,10,11,12,13},out[8];MemRef2 ad=two(a,2,4),od=two(out,4,2);
  _mlir_ciface_values(&ad,&od);int errors=0;
  for(int i=0;i<4;++i)for(int j=0;j<2;++j)errors+=out[i*2+j]!=a[j*4+i]+1;
  report("transpose-value",8,errors);printf("sample\ttranspose\t%.0f\t%.0f\t%.0f\t%.0f\n",out[0],out[1],out[6],out[7]);
  float data[]={1,2,3,4};MemRef1 rd=one(data,4);float r=_mlir_ciface_reduction(&rd);
  report("reduce",4,r!=10);printf("sample\treduce\t%.0f\n",r);
  float cancellation[]={1e20f,1,-1e20f,3};rd=one(cancellation,4);r=_mlir_ciface_reduction(&rd);
  report("ordered-reduce",4,r!=3);printf("sample\tordered-reduce\t%.0f\n",r);
  float lhs[]={1,2,3,4,5,6},rhs[]={7,8,9,10,11,12},acc[]={1,1,1,1};
  MemRef2 ld=two(lhs,2,3),bd=two(rhs,3,2),cd=two(acc,2,2);_mlir_ciface_dot(&ld,&bd,&cd);
  float ref[]={59,65,140,155};errors=0;for(int k=0;k<4;++k)errors+=acc[k]!=ref[k];
  report("contract",4,errors);printf("sample\tcontract\t%.0f\t%.0f\t%.0f\t%.0f\n",acc[0],acc[1],acc[2],acc[3]);
  return failed!=0;
}
