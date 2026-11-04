#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sched.h>
typedef struct {float*allocated,*aligned;int64_t offset,sizes[1],strides[1];} MemRef1;
extern void _mlir_ciface_scalar(MemRef1*,MemRef1*);
extern void _mlir_ciface_automatic(MemRef1*,MemRef1*);
extern void _mlir_ciface_split(MemRef1*,MemRef1*);
static volatile double sink;
static double now(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))exit(2);return t.tv_sec+1e-9*t.tv_nsec;}
static int cmp(const void*a,const void*b){double x=*(const double*)a,y=*(const double*)b;return (x>y)-(x<y);}
int main(void){
  cpu_set_t available,chosen;
  if(sched_getaffinity(0,sizeof(available),&available))return 2;
  int cpu=0;while(cpu<CPU_SETSIZE&&!CPU_ISSET(cpu,&available))++cpu;
  if(cpu==CPU_SETSIZE)return 2;
  CPU_ZERO(&chosen);CPU_SET(cpu,&chosen);if(sched_setaffinity(0,sizeof(chosen),&chosen))return 2;
  printf("cpu\t%d\n",cpu);
  const char*names[]={"scalar","automatic","split"};
  void(*f[])(MemRef1*,MemRef1*)={_mlir_ciface_scalar,_mlir_ciface_automatic,_mlir_ciface_split};
  const int sizes[]={1024,65536,4194304};
  for(int s=0;s<3;++s){
    int n=sizes[s],reps=8388608/n;if(reps<3)reps=3;
    float*x=malloc(n*sizeof(float)),*y=malloc(n*sizeof(float));if(!x||!y)return 2;
    for(int k=0;k<n;++k)x[k]=(float)(k%127-63);
    MemRef1 a={x,x,0,{n},{1}},b={y,y,0,{n},{1}};
    for(int v=0;v<3;++v){
      f[v](&a,&b);for(int k=0;k<n;++k)if(y[k]!=2*(x[k]+1))return 1;
      for(int w=0;w<8;++w)f[v](&a,&b);
    }
    double times[3][9];
    for(int trial=0;trial<9;++trial)for(int z=0;z<3;++z){
      int v=(trial+z)%3;double start=now();for(int r=0;r<reps;++r)f[v](&a,&b);
      times[v][trial]=(now()-start)*1e9/reps;
      sink+=y[trial]+y[n-1-trial];
      printf("raw\t%s\t%d\t%d\t%d\t%.3f\n",names[v],n,reps,trial,times[v][trial]);
    }
    for(int v=0;v<3;++v){
      qsort(times[v],9,sizeof(double),cmp);
      printf("bench\t%s\t%d\t%d\t%.3f\t%.3f\t%.3f\n",names[v],n,reps,times[v][0],times[v][4],times[v][8]);
    }
    free(x);free(y);
  }
  printf("checksum\t%.0f\n",sink);return 0;
}
