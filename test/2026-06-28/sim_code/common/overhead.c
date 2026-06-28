#include <stdio.h>
#include <string.h>
#include <time.h>
#include "api.h"
enum { FP_NONE=0 }; enum { FM_NONE=0 }; enum { CM_BASE=0,CM_IRV,CM_LEEHA };
extern int sign_fi(unsigned char*,size_t*,const unsigned char*,size_t,
                   const unsigned char*,size_t,const unsigned char*,const unsigned char*);
extern int g_fp,g_fm,g_cm,g_irv_detected,g_leeha_detected,g_iter;
static unsigned char sk[CRYPTO_SECRETKEYBYTES],pk[CRYPTO_PUBLICKEYBYTES],rnd[32];
static const unsigned char M[3]={'m','s','g'}; static unsigned char PRE[1]={0};
static int run(unsigned char*s,size_t*l,int cm){g_fp=0;g_fm=0;g_cm=cm;g_irv_detected=0;g_leeha_detected=0;g_iter=0;return sign_fi(s,l,M,3,PRE,1,rnd,sk);}
static double now(){struct timespec t;clock_gettime(CLOCK_PROCESS_CPUTIME_ID,&t);return t.tv_sec*1e9+t.tv_nsec;}
int main(){
  memset(rnd,7,32); crypto_sign_keypair(pk,sk);
  unsigned char s[CRYPTO_BYTES],s2[CRYPTO_BYTES]; size_t l,l2; volatile long acc=0;
  int N=400;
  for(int i=0;i<30;i++) acc+=run(s,&l,CM_BASE); // warmup
  double t0=now(); for(int i=0;i<N;i++) acc+=run(s,&l,CM_BASE); double tb=now()-t0;
  t0=now(); for(int i=0;i<N;i++) acc+=run(s,&l,CM_IRV); double ti=now()-t0;
  t0=now(); for(int i=0;i<N;i++){run(s,&l,CM_LEEHA); acc+=crypto_sign_verify(s,l,M,3,PRE,0,pk);} double tl=now()-t0;
  t0=now(); for(int i=0;i<N;i++){run(s,&l,CM_BASE); run(s2,&l2,CM_BASE); acc+=memcmp(s,s2,l);} double td=now()-t0;
  printf("baseline,1.000\nirv,%.3f\nleeha,%.3f\ndouble_comp,%.3f\n", ti/tb, tl/tb, td/tb);
  fprintf(stderr,"(N=%d, CLOCK_PROCESS_CPUTIME_ID; 절대치는 STM32F4 실측)\n",N);
  return (int)acc&0;
}
