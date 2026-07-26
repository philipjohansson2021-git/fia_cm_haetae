#include <stdio.h>
#include <string.h>
#include <time.h>
#include "api.h"
#include <signal.h>
#include <setjmp.h>
static sigjmp_buf g_jb; static volatile int g_crash=0;
static void on_sig(int sig){ (void)sig; g_crash=1; siglongjmp(g_jb,1); }
enum { FP_NONE=0,FP_KEYMEM,FP_SEED,FP_Y,FP_SIGNBIT,FP_CHALLENGE,FP_CS1,FP_ADDY,FP_REJECT,FP_UNPACKA,FP_COMMIT,FP_LSB,FP_HINT };
enum { FM_NONE=0,FM_SKIP,FM_ZERO,FM_BITFLIP,FM_BYTEFLIP,FM_SETCONST,FM_LOOPABORT };
enum { CM_BASE=0,CM_IRV,CM_LEEHA };
extern int sign_fi(unsigned char*,size_t*,const unsigned char*,size_t,
                   const unsigned char*,size_t,const unsigned char*,const unsigned char*);
extern int g_fp,g_fm,g_cm,g_irv_detected,g_leeha_detected,g_iter;
static unsigned char sk[CRYPTO_SECRETKEYBYTES], pk[CRYPTO_PUBLICKEYBYTES], rnd[32];
static unsigned char gsig[CRYPTO_BYTES]; static size_t gslen;
static const unsigned char MSG[3]={'m','s','g'}; static unsigned char PRE[1]={0};

static int run(unsigned char*sig,size_t*slen,int fp,int fm,int cm){
  g_fp=fp; g_fm=fm; g_cm=cm; g_irv_detected=0; g_leeha_detected=0; g_iter=0; g_crash=0;
  if(sigsetjmp(g_jb,1)){ return 3; }   /* 3 = crash(키 복구 불가) */
  return sign_fi(sig,slen,MSG,3,PRE,1,rnd,sk);
}
static int vrfy(unsigned char*sig,size_t slen){ return crypto_sign_verify(sig,slen,MSG,3,PRE,0,pk); }

const char* FPN[]={"none","key_mem","seed_gen","y_sample","sign_bit","challenge","cs1_mul(T1)","add_y(T2)","reject(RB)","unpackA","commit_Ay","lsb","hint"};
const char* FMN[]={"none","skip","zeroing","bitflip","byteflip","set_const","loop_abort"};

int main(void){
  setvbuf(stdout,NULL,_IONBF,0);
  signal(SIGSEGV,on_sig); signal(SIGFPE,on_sig); signal(SIGABRT,on_sig);
  memset(rnd,7,32);
  crypto_sign_keypair(pk,sk);
  run(gsig,&gslen,FP_NONE,FM_NONE,CM_BASE);   // golden + golden_ck 캡처
  int POINTS[]={FP_KEYMEM,FP_SEED,FP_Y,FP_SIGNBIT,FP_CHALLENGE,FP_CS1,FP_ADDY,FP_REJECT,FP_UNPACKA,FP_COMMIT,FP_LSB,FP_HINT};
  int MODELS[]={FM_SKIP,FM_ZERO,FM_BITFLIP,FM_BYTEFLIP,FM_SETCONST,FM_LOOPABORT};
  unsigned char s[CRYPTO_BYTES]; size_t sl;

  printf("point,model,base_ret,base_faulty,base_verify,irv_det,leeha_det,double_det\n");
  for(int pi=0;pi<12;pi++) for(int mi=0;mi<6;mi++){
    int fp=POINTS[pi], fm=MODELS[mi];
    fprintf(stderr,"try %s/%s\n",FPN[fp],FMN[fm]);
    // baseline
    int br=run(s,&sl,fp,fm,CM_BASE);
    int faulty = (br==0) ? (memcmp(s,gsig, br==0?sl:0)!=0 || sl!=gslen) : 0;
    int bv = (br==0)? vrfy(s,sl) : -1;
    // irv
    int ir=run(s,&sl,fp,fm,CM_IRV);  int irv_det = g_irv_detected || ir==2;
    // leeha (sanity + sign-then-verify)
    int lr=run(s,&sl,fp,fm,CM_LEEHA);
    int leeha_det = g_leeha_detected || lr==2 || (lr==0 && vrfy(s,sl)!=0);
    // double: 일시적 결함이면 두 실행 상이->탐지. 영속(key_mem)은 미탐.
    int double_det = (faulty && fp!=FP_KEYMEM) ? 1 : (br==2?1:0);
    printf("%s,%s,%d,%d,%d,%d,%d,%d\n",FPN[fp],FMN[fm],br,faulty,bv,irv_det,leeha_det,double_det);
  }

  // ---- 오버헤드(상대): x86 cycles via clock(), N회 평균 (무결함) ----
  #define NREP 200
  unsigned char tmp[CRYPTO_BYTES]; size_t tl; volatile int acc=0;
  clock_t t0,t1; double tb,ti,tl_,td;
  t0=clock(); for(int i=0;i<NREP;i++){ acc+=run(tmp,&tl,FP_NONE,FM_NONE,CM_BASE);} t1=clock(); tb=(double)(t1-t0);
  t0=clock(); for(int i=0;i<NREP;i++){ acc+=run(tmp,&tl,FP_NONE,FM_NONE,CM_IRV);} t1=clock(); ti=(double)(t1-t0);
  t0=clock(); for(int i=0;i<NREP;i++){ run(tmp,&tl,FP_NONE,FM_NONE,CM_LEEHA); acc+=vrfy(tmp,tl);} t1=clock(); tl_=(double)(t1-t0);
  t0=clock(); for(int i=0;i<NREP;i++){ run(tmp,&tl,FP_NONE,FM_NONE,CM_BASE); unsigned char t2[CRYPTO_BYTES]; size_t l2; run(t2,&l2,FP_NONE,FM_NONE,CM_BASE); acc+=memcmp(tmp,t2,tl);} t1=clock(); td=(double)(t1-t0);
  fprintf(stderr,"OVERHEAD baseline=1.000 irv=%.3f leeha=%.3f double=%.3f (N=%d, x86 clock; 절대치는 STM32F4 실측)\n",
          ti/tb, tl_/tb, td/tb, NREP);
  return 0;
}
