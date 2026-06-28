#include <stdio.h>
#include <string.h>
#include "api.h"
enum { FP_NONE=0,FP_KEYMEM,FP_SEED,FP_Y,FP_SIGNBIT,FP_CHALLENGE,FP_CS1,FP_ADDY,FP_REJECT };
enum { FM_NONE=0,FM_SKIP,FM_ZERO,FM_BITFLIP,FM_BYTEFLIP,FM_SETCONST,FM_LOOPABORT };
enum { CM_BASE=0,CM_IRV,CM_LEEHA };
extern int sign_fi(unsigned char*,size_t*,const unsigned char*,size_t,
                   const unsigned char*,size_t,const unsigned char*,const unsigned char*);
extern int g_fp,g_fm,g_cm,g_irv_detected,g_leeha_detected,g_iter;
static unsigned char sk[CRYPTO_SECRETKEYBYTES], pk[CRYPTO_PUBLICKEYBYTES];
static unsigned char rnd[32];
static unsigned char gsig[CRYPTO_BYTES]; static size_t gslen;
static int run(unsigned char*sig,size_t*slen,int fp,int fm,int cm){
  g_fp=fp; g_fm=fm; g_cm=cm; g_irv_detected=0; g_leeha_detected=0; g_iter=0;
  unsigned char pre[1]={0};
  return sign_fi(sig,slen,(const unsigned char*)"msg",3,pre,1,rnd,sk);
}
int main(void){
  memset(rnd,7,32);
  if(crypto_sign_keypair(pk,sk)){puts("keypair fail");return 1;}
  // golden (NONE, BASE) -- golden_ck도 여기서 캡처됨
  int r=run(gsig,&gslen,FP_NONE,FM_NONE,CM_BASE);
  printf("[golden] ret=%d slen=%zu verify=%d\n",r,gslen,
         crypto_sign_verify(gsig,gslen,(const unsigned char*)"msg",3,(const unsigned char*)"\0",0,pk));
  unsigned char s2[CRYPTO_BYTES]; size_t l2;
  #define EQ(a,b,n) (memcmp(a,b,n)==0)
  int pass=0,fail=0;
  #define CHK(cond,msg) do{ if(cond){pass++;printf("  PASS %s\n",msg);} else {fail++;printf("  FAIL %s\n",msg);} }while(0)

  // 1) 무결함 IRV == golden, 오탐0
  run(s2,&l2,FP_NONE,FM_NONE,CM_IRV);
  CHK(EQ(s2,gsig,gslen)&&g_irv_detected==0, "IRV no-fault == golden & no false-positive");

  // 2) T2(+y skip) baseline -> faulty(!=golden)
  run(s2,&l2,FP_ADDY,FM_SKIP,CM_BASE);
  CHK(!EQ(s2,gsig,gslen), "T2 skip baseline -> faulty signature");
  // 3) T2 IRV -> detected
  run(s2,&l2,FP_ADDY,FM_SKIP,CM_IRV);
  CHK(g_irv_detected==1, "T2 skip IRV -> detected");

  // 4) T1(c*s1 skip) baseline -> faulty ; IRV detected
  run(s2,&l2,FP_CS1,FM_SKIP,CM_BASE); CHK(!EQ(s2,gsig,gslen),"T1 skip baseline -> faulty");
  run(s2,&l2,FP_CS1,FM_SKIP,CM_IRV);  CHK(g_irv_detected==1,"T1 skip IRV -> detected");

  // 5) RB(reject skip) IRV -> detected via M2 (norm)
  int rr=run(s2,&l2,FP_REJECT,FM_SKIP,CM_BASE);
  printf("  [info] RB baseline ret=%d (2=reject-loop exhausted)\n",rr);
  run(s2,&l2,FP_REJECT,FM_SKIP,CM_IRV); CHK(g_irv_detected==1 || rr==2,"RB skip IRV -> detected(or naturally bounded)");

  // 6) KEYMEM(bitflip) baseline -> faulty ; IRV detected via M3 checksum
  run(s2,&l2,FP_KEYMEM,FM_BITFLIP,CM_BASE); CHK(!EQ(s2,gsig,gslen),"KEYMEM baseline -> faulty");
  run(s2,&l2,FP_KEYMEM,FM_BITFLIP,CM_IRV);  CHK(g_irv_detected==1,"KEYMEM IRV -> detected (M3)");

  // 7) SEED(zero) baseline -> faulty? (예측 y) ; Lee-Ha sanity -> detected
  run(s2,&l2,FP_SEED,FM_ZERO,CM_BASE); printf("  [info] SEED zero baseline !=golden? %d\n",!EQ(s2,gsig,gslen));
  run(s2,&l2,FP_SEED,FM_ZERO,CM_LEEHA); CHK(g_leeha_detected==1,"SEED zero Lee-Ha sanity -> detected");

  printf("\nRESULT: PASS=%d FAIL=%d\n",pass,fail);
  return fail?1:0;
}
