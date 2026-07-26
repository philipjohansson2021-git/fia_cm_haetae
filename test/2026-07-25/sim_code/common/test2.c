#include <stdio.h>
#include <string.h>
#include "api.h"
enum { FP_NONE=0,FP_KEYMEM,FP_SEED,FP_Y,FP_SIGNBIT,FP_CHALLENGE,FP_CS1,FP_ADDY,FP_REJECT };
enum { FM_NONE=0,FM_SKIP,FM_ZERO,FM_BITFLIP,FM_BYTEFLIP,FM_SETCONST,FM_LOOPABORT };
enum { CM_BASE=0,CM_IRV,CM_LEEHA,CM_IRI };
extern int sign_fi(unsigned char*,size_t*,const unsigned char*,size_t,
                   const unsigned char*,size_t,const unsigned char*,const unsigned char*);
extern int g_fp,g_fm,g_cm,g_irv_detected,g_leeha_detected,g_iter;
extern int g_iri_detected;
static unsigned char sk[CRYPTO_SECRETKEYBYTES], pk[CRYPTO_PUBLICKEYBYTES];
static unsigned char rnd[32];
static unsigned char gsig[CRYPTO_BYTES]; static size_t gslen;
static int run(unsigned char*sig,size_t*slen,int fp,int fm,int cm){
  g_fp=fp; g_fm=fm; g_cm=cm; g_irv_detected=0; g_leeha_detected=0; g_iri_detected=0; g_iter=0;
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

  // ===== WITNESS (CM_IRI): 경량 T1 부분재계산 + T2 재덧셈 지문 + RB + 키체크섬 =====
  // 8) 무결함 witness == golden & 오탐0  (= 스쿨북 정확성 self-test: 틀리면 여기서 FP 발생)
  run(s2,&l2,FP_NONE,FM_NONE,CM_IRI);
  CHK(EQ(s2,gsig,gslen)&&g_iri_detected==0, "IRI no-fault == golden & no FP (schoolbook exact)");
  // 9) T2(+y skip) witness -> detected (재덧셈 지문)
  run(s2,&l2,FP_ADDY,FM_SKIP,CM_IRI);  CHK(g_iri_detected==1,"T2 skip IRI(witness) -> detected");
  // 10) T1(c*s skip) witness -> detected (부분계수 재계산)
  run(s2,&l2,FP_CS1,FM_SKIP,CM_IRI);   CHK(g_iri_detected==1,"T1 skip IRI(witness) -> detected");
  // 11) T1(bitflip coeff0) witness -> detected (인덱스 0 포함 검사)
  run(s2,&l2,FP_CS1,FM_BITFLIP,CM_IRI);CHK(g_iri_detected==1,"T1 bitflip IRI(witness) -> detected");
  // 12) RB(reject skip) witness -> detected via 노름 재검사 (or 자연 bound)
  int rr2=run(s2,&l2,FP_REJECT,FM_SKIP,CM_BASE);
  run(s2,&l2,FP_REJECT,FM_SKIP,CM_IRI);CHK(g_iri_detected==1||rr2==2,"RB skip IRI(witness) -> detected(or bounded)");
  // 13) KEYMEM witness -> detected via 체크섬
  run(s2,&l2,FP_KEYMEM,FM_BITFLIP,CM_IRI);CHK(g_iri_detected==1,"KEYMEM IRI(witness) -> detected (checksum)");

  // 14) robustness: N개 무작위(msg,rnd) → witness 무결함==그 run의 golden & 오탐0; T2 매번 탐지
  { int N=200, fp_cnt=0, miss=0; unsigned char gg[CRYPTO_BYTES], ww[CRYPTO_BYTES]; size_t gl, wl;
    for (int t=0; t<N; t++) {
      unsigned char r2[32]; for (int j=0;j<32;j++) r2[j]=(unsigned char)(t*31+j*7+1);
      char msg[12]; int ml=snprintf(msg,sizeof msg,"m%d",t);
      g_fp=FP_NONE;g_fm=FM_NONE;g_cm=CM_BASE;g_irv_detected=0;g_leeha_detected=0;g_iri_detected=0;g_iter=0;
      sign_fi(gg,&gl,(const unsigned char*)msg,ml,(const unsigned char*)"\0",1,r2,sk);
      g_fp=FP_NONE;g_fm=FM_NONE;g_cm=CM_IRI;g_irv_detected=0;g_leeha_detected=0;g_iri_detected=0;g_iter=0;
      sign_fi(ww,&wl,(const unsigned char*)msg,ml,(const unsigned char*)"\0",1,r2,sk);
      if (g_iri_detected || wl!=gl || memcmp(ww,gg,gl)) fp_cnt++;      /* 오탐 */
      g_fp=FP_ADDY;g_fm=FM_SKIP;g_cm=CM_IRI;g_irv_detected=0;g_leeha_detected=0;g_iri_detected=0;g_iter=0;
      sign_fi(ww,&wl,(const unsigned char*)msg,ml,(const unsigned char*)"\0",1,r2,sk);
      if (!g_iri_detected) miss++;                                    /* T2 미탐 */
    }
    printf("  [robust] N=%d  witness false-positive=%d  T2 miss=%d\n",N,fp_cnt,miss);
    CHK(fp_cnt==0 && miss==0, "IRI robustness: 0 false-positive & 0 T2-miss over N random");
  }

  printf("\nRESULT: PASS=%d FAIL=%d\n",pass,fail);
  return fail?1:0;
}
