#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { int32_t *allocated,*aligned; int64_t offset,sizes[2],strides[2]; } MemRef2;
extern void _mlir_ciface_crop(MemRef2*,MemRef2*,int64_t,int64_t);
extern void _mlir_ciface_triangle(MemRef2*);
extern void _mlir_ciface_affine_add(MemRef2*,MemRef2*);
extern void _mlir_ciface_affine_tiled(MemRef2*,MemRef2*);
extern void _mlir_ciface_wave(MemRef2*);
extern void _mlir_ciface_wave_wrong(MemRef2*);
extern void _mlir_ciface_elementwise_base(MemRef2*,MemRef2*);
extern void _mlir_ciface_elementwise_fused(MemRef2*,MemRef2*);
extern void _mlir_ciface_elementwise_tiled(MemRef2*,MemRef2*);
extern void _mlir_ciface_elementwise_swapped(MemRef2*,MemRef2*);
static int failed;
static MemRef2 desc(int32_t*p,int64_t m,int64_t n){MemRef2 d={p,p,0,{m,n},{n,1}};return d;}
static int32_t get(MemRef2 d,int64_t i,int64_t j){return d.aligned[d.offset+i*d.strides[0]+j*d.strides[1]];}
static void report(const char *name,int count,int errors){printf("case\t%s\t%d\t%d\n",name,count,errors);failed+=errors!=0;}
static void elementwise_case(int m,int n){
  const char *names[]={"base","fused","tiled","swapped"};
  void(*functions[])(MemRef2*,MemRef2*)={_mlir_ciface_elementwise_base,_mlir_ciface_elementwise_fused,
    _mlir_ciface_elementwise_tiled,_mlir_ciface_elementwise_swapped};
  int count=m*n;int32_t *data=malloc((count+1)*sizeof(int32_t));if(!data)exit(2);
  for(int k=0;k<count;++k)data[k]=k*3-12;
  MemRef2 in=desc(data,m,n);
  for(int f=0;f<4;++f){
    MemRef2 out;functions[f](&out,&in);int errors=out.sizes[0]!=m || out.sizes[1]!=n;
    for(int i=0;i<m;++i)for(int j=0;j<n;++j){
      int k=i*n+j;errors+=get(out,i,j)!=2*(k*3-11);errors+=data[k]!=k*3-12;
    }
    char label[80];snprintf(label,sizeof(label),"elementwise-%s-%dx%d",names[f],m,n);report(label,count,errors);
    free(out.allocated);
  }
  free(data);
}
int main(void){
  _Static_assert(sizeof(void*)==8,"64-bit host ABI required");
  int32_t source[48], cropped[14];for(int i=0;i<6;++i)for(int j=0;j<8;++j)source[i*8+j]=100*i+j;
  for(int i=0;i<14;++i)cropped[i]=-777;
  MemRef2 src=desc(source,6,8),crop=desc(cropped+1,3,4);_mlir_ciface_crop(&src,&crop,1,2);
  int errors=cropped[0]!=-777 || cropped[13]!=-777;
  for(int i=0;i<3;++i)for(int j=0;j<4;++j)errors+=cropped[1+i*4+j]!=100*(i+1)+j+2;
  report("crop",12,errors);printf("sample\tcrop-corners\t%d\t%d\n",cropped[1],cropped[12]);
  int32_t triangle[16];MemRef2 tri=desc(triangle,4,4);_mlir_ciface_triangle(&tri);errors=0;
  for(int i=0;i<4;++i)for(int j=0;j<4;++j)errors+=triangle[i*4+j]!=(i>=j);report("triangle",16,errors);
  int32_t a[35],out1[37],out2[37];for(int k=0;k<35;++k)a[k]=k-17;
  for(int k=0;k<37;++k)out1[k]=out2[k]=-777;
  MemRef2 ad=desc(a,5,7),o1=desc(out1+1,5,7),o2=desc(out2+1,5,7);
  _mlir_ciface_affine_add(&ad,&o1);_mlir_ciface_affine_tiled(&ad,&o2);errors=0;
  for(int k=0;k<35;++k)errors+=out1[k+1]!=a[k]+1 || out2[k+1]!=a[k]+1;
  errors+=out1[0]!=-777 || out1[36]!=-777 || out2[0]!=-777 || out2[36]!=-777;
  report("affine-tiling",35,errors);
  int32_t wave[35],wrong[35],ref[35];
  for(int i=0;i<5;++i)for(int j=0;j<7;++j)wave[i*7+j]=wrong[i*7+j]=ref[i*7+j]=100*i+j;
  for(int i=1;i<5;++i)for(int j=0;j<6;++j)ref[i*7+j]=ref[(i-1)*7+j+1]+1;
  MemRef2 wd=desc(wave,5,7),bad=desc(wrong,5,7);_mlir_ciface_wave(&wd);_mlir_ciface_wave_wrong(&bad);
  errors=memcmp(wave,ref,sizeof(wave))!=0;report("wave-reference",35,errors);
  report("wrong-interchange-detected",35,memcmp(wrong,wave,sizeof(wave))==0);
  printf("sample\twave-at-2-0\t%d\t%d\n",wave[14],wrong[14]);
  elementwise_case(5,7);elementwise_case(1,1);elementwise_case(1,7);elementwise_case(2,3);
  elementwise_case(0,7);elementwise_case(5,0);elementwise_case(7,5);
  return failed!=0;
}
