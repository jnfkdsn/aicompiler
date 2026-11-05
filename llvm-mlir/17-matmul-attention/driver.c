#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { float *allocated, *aligned; int64_t offset, size[2], stride[2]; } M2;
typedef struct { int64_t *allocated, *aligned; int64_t offset, size, stride; } I1;
extern void _mlir_ciface_matmul(M2 *, M2 *, M2 *);
extern void _mlir_ciface_tiled(M2 *, M2 *, M2 *);
extern void _mlir_ciface_unrolled(M2 *, M2 *, M2 *);
extern void _mlir_ciface_attention(M2 *, M2 *, M2 *, M2 *, I1 *, float);
extern void _mlir_ciface_online(M2 *, M2 *, M2 *, M2 *, I1 *, float);
static int failed;
static float *storage(int64_t count) {
  float *p = malloc((size_t)(count + 2) * sizeof(float));
  if (!p) exit(2);
  p[0] = p[count + 1] = 123456.0f;
  for (int64_t i = 1; i <= count; ++i) p[i] = -777.0f;
  return p;
}
static M2 descriptor(float *p, int64_t m, int64_t n) {
  M2 d = {p, p + 1, 0, {m, n}, {n, 1}};
  return d;
}
static int guard(float *p, int64_t count) {
  return p[0] == 123456.0f && p[count + 1] == 123456.0f;
}
static double sample(int64_t x) { return (double)((x * 7 + 3) % 17 - 8) * 0.125; }
static void matmul(int64_t m, int64_t n, int64_t k) {
  float *a = storage(m*k), *b = storage(k*n), *c = storage(m*n);
  for (int64_t i=0;i<m*k;++i) a[i+1]=(float)sample(i);
  for (int64_t i=0;i<k*n;++i) b[i+1]=(float)sample(i+2);
  M2 ad=descriptor(a,m,k), bd=descriptor(b,k,n), cd=descriptor(c,m,n);
  void (*variants[])(M2 *,M2 *,M2 *)={_mlir_ciface_matmul,_mlir_ciface_tiled,_mlir_ciface_unrolled};
  const char *names[]={"scalar","tiled","unrolled"};
  for(int s=0;s<3;++s) {
    for(int64_t i=0;i<m*n;++i)c[i+1]=-777.0f;
    variants[s](&ad,&bd,&cd);
    int ok=guard(a,m*k)&&guard(b,k*n)&&guard(c,m*n);
    double error=0;
    for(int64_t i=0;i<m;++i)for(int64_t j=0;j<n;++j) {
      double ref=0;
      for(int64_t h=0;h<k;++h)ref+=(double)a[1+i*k+h]*b[1+h*n+j];
      double diff=fabs((double)c[1+i*n+j]-ref);
      error=fmax(error,diff);ok &= isfinite(c[1+i*n+j])&&diff<=1e-5+1e-5*fabs(ref);
    }
    printf("matmul\t%s\t%ldx%ldx%ld\t%.9g\t%d\n",names[s],(long)m,(long)n,(long)k,error,ok);
    failed+=!ok;
  }
  free(a);free(b);free(c);
}
static void attention(const char *name,int64_t m,int64_t n,int64_t d,int64_t p,int mode) {
  float *q=storage(m*d),*k=storage(n*d),*v=storage(n*p),*o=storage(m*p);
  int64_t *lengths=malloc((size_t)(m+1)*sizeof(int64_t));
  if(!lengths)exit(2);
  for(int64_t i=0;i<m*d;++i)q[i+1]=(float)sample(i);
  for(int64_t i=0;i<n*d;++i)k[i+1]=(float)sample(i+5);
  for(int64_t i=0;i<n*p;++i)v[i+1]=(float)sample(i+9);
  float scale=1.0f/sqrtf((float)d);
  if(mode>=4) {
    for(int64_t i=0;i<m*d;++i)q[i+1]=1;
    for(int64_t j=0;j<n;++j)for(int64_t h=0;h<d;++h)
      k[1+j*d+h]=mode==4?(j==3?logf(2.0f):0.0f):(1000.0f+(float)j);
    if(mode==4)for(int64_t j=0;j<n;++j)v[1+j*p]=10.0f*(float)(j+1);
    scale=1;
  }
  for(int64_t i=0;i<m;++i)lengths[i]=mode==1?(i+1<n?i+1:n):mode==2?(i%2?n:0):mode==3?0:n;
  I1 ld={lengths,lengths,0,m,1};
  M2 qd=descriptor(q,m,d),kd=descriptor(k,n,d),vd=descriptor(v,n,p),od=descriptor(o,m,p);
  void (*variants[])(M2 *,M2 *,M2 *,M2 *,I1 *,float)={_mlir_ciface_attention,_mlir_ciface_online};
  const char *names[]={"materialized","online"};
  double *scores=malloc((size_t)(n+1)*sizeof(double));
  if(!scores)exit(2);
  for(int s=0;s<2;++s) {
    for(int64_t i=0;i<m*p;++i)o[1+i]=-777;
    variants[s](&qd,&kd,&vd,&od,&ld,scale);
    int ok=guard(q,m*d)&&guard(k,n*d)&&guard(v,n*p)&&guard(o,m*p);
    double error=0;
    for(int64_t i=0;i<m;++i) {
      double max=-INFINITY,denom=0;
      for(int64_t j=0;j<lengths[i];++j) {
        scores[j]=0;
        for(int64_t h=0;h<d;++h)scores[j]+=(double)q[1+i*d+h]*k[1+j*d+h];
        scores[j]*=(double)scale;max=fmax(max,scores[j]);
      }
      for(int64_t j=0;j<lengths[i];++j) {scores[j]=exp(scores[j]-max);denom+=scores[j];}
      for(int64_t c=0;c<p;++c) {
        double ref=0;
        for(int64_t j=0;j<lengths[i];++j)ref+=scores[j]*v[1+j*p+c];
        if(lengths[i])ref/=denom;
        double actual=o[1+i*p+c],diff=fabs(actual-ref);
        error=fmax(error,diff);ok &= isfinite(actual)&&diff<=3e-5+3e-5*fabs(ref);
        if(mode==4)printf("value\t%s\t%.9g\t%.17g\n",names[s],actual,ref);
      }
    }
    printf("attention\t%s\t%s\t%.9g\t%d\n",names[s],name,error,ok);failed+=!ok;
  }
  free(q);free(k);free(v);free(o);free(lengths);free(scores);
}
int main(void) {
  _Static_assert(sizeof(void*)==8,"64-bit descriptor and index ABI required");
  const int64_t shapes[][3]={{2,2,3},{5,7,11},{1,1,1},{4,6,8},{2,3,0},{0,3,5},{3,0,5},{3,5,17}};
  for(size_t i=0;i<sizeof(shapes)/sizeof(shapes[0]);++i)matmul(shapes[i][0],shapes[i][1],shapes[i][2]);
  attention("rescale-example",1,4,1,1,4);
  attention("one-key",3,1,4,2,0);
  attention("tail",5,7,3,5,0);
  attention("exact-tile",2,6,4,3,0);
  attention("causal-prefix",5,7,3,5,1);
  attention("mixed-empty",4,5,3,2,2);
  attention("all-masked",2,4,3,2,3);
  attention("shifted",2,7,1,2,5);
  attention("empty-batch",0,4,3,2,0);
  attention("empty-keys",2,0,3,2,0);
  attention("empty-value-width",2,4,3,0,0);
  attention("longer-row",2,17,5,7,0);
  return failed!=0;
}
