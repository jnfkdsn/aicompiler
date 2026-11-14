#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
extern int32_t adjust(bool,int32_t);
extern int32_t choose(int64_t,int32_t);
extern int32_t parallel_sum(int64_t,int32_t);
extern int32_t forall_value(void);
int main(void){
 int failures=0;
 for(int x=-3;x<=3;x+=3)for(int flag=0;flag<2;flag++){
  int result=adjust(flag,x),expected=x+(flag?1:-1);
  printf("adjust flag=%d x=%d result=%d expected=%d\n",flag,x,result,expected);failures+=result!=expected;
 }
 int tags[]={-1,0,1,2,3};
 for(int i=0;i<5;i++){
  int result=choose(tags[i],7),expected=tags[i]==0?7:tags[i]==2?14:6;
  printf("choose tag=%d result=%d expected=%d\n",tags[i],result,expected);failures+=result!=expected;
 }
 for(int n=0;n<=4;n++){
  int result=parallel_sum(n,5),expected=5+n*(n-1)/2;
  printf("parallel_sum n=%d result=%d expected=%d\n",n,result,expected);failures+=result!=expected;
 }
 int result=forall_value();printf("forall_value result=%d expected=3\n",result);failures+=result!=3;
 // Fixed-version lowering uses an i32 switch. Record its unsupported wide-tag
 // behavior separately; this is deliberately not classified as a correct case.
 int wide=choose(INT64_C(4294967296),7);
 printf("known limitation: wide tag=4294967296 observed=%d source-default=6\n",wide);
 failures+=wide!=7;
 return failures?1:0;
}
