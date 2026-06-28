// SPDX-License-Identifier: MIT
// sign_fi.c : 실제 HAETAE 전체 서명에 결함을 주입하는 계측 서명 (x86 시뮬용)
// 원본 src/sign.c 의 crypto_sign_signature_internal 을 패치하여 생성.
#include "api.h"
#include "packing.h"
#include "params.h"
#include "poly.h"
#include "polyfix.h"
#include "polymat.h"
#include "polyvec.h"
#include "randombytes.h"
#include "symmetric.h"
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* ---- 결함점/결함모델/대응기법 제어 (harness가 설정) ---- */
enum { FP_NONE=0, FP_KEYMEM, FP_SEED, FP_Y, FP_SIGNBIT, FP_CHALLENGE, FP_CS1, FP_ADDY, FP_REJECT, FP_UNPACKA, FP_COMMIT, FP_LSB, FP_HINT };
enum { FM_NONE=0, FM_SKIP, FM_ZERO, FM_BITFLIP, FM_BYTEFLIP, FM_SETCONST, FM_LOOPABORT };
enum { CM_BASE=0, CM_IRV, CM_LEEHA };
#define FI_MAX_ITER 4000
int g_fp=FP_NONE, g_fm=FM_NONE, g_cm=CM_BASE;
int g_irv_detected=0, g_leeha_detected=0, g_iter=0;
uint32_t g_golden_ck=0, g_cur_ck=0; int g_have_golden_ck=0;

static void fi_reset(int fp,int fm,int cm){ g_fp=fp; g_fm=fm; g_cm=cm; g_irv_detected=0; g_leeha_detected=0; g_iter=0; }

static uint32_t fi_polyvecm_ck(const polyvecm *s){
  uint32_t h=2166136261u; const int32_t *p=(const int32_t*)s;
  for (size_t i=0;i<sizeof(polyvecm)/4;i++){ h^=(uint32_t)p[i]; h*=16777619u; } return h; }
static void fi_corrupt_polyvecm(polyvecm *s, int fm){
  int32_t *p=(int32_t*)s;
  if (fm==FM_ZERO||fm==FM_SKIP) p[0]=0;
  else if (fm==FM_BITFLIP) p[0]^=1;
  else if (fm==FM_BYTEFLIP) ((uint8_t*)p)[0]^=0xFF;
  else if (fm==FM_SETCONST) p[0]=777;
  else p[0]+=1; }
static void fi_fault_buf(uint8_t *b,size_t n,int fm){
  if (fm==FM_SKIP||fm==FM_ZERO) memset(b,0,n);
  else if (fm==FM_SETCONST) memset(b,0x5A,n);
  else if (fm==FM_BITFLIP) b[0]^=1;
  else if (fm==FM_BYTEFLIP) b[0]^=0xFF;
  else memset(b,0,n); }
static int fi_buf_degenerate(const uint8_t *b,size_t n){
  int allz=1, alls=1; for(size_t i=0;i<n;i++){ if(b[i])allz=0; if(b[i]!=b[0])alls=0; } return allz||alls; }
static void fi_fault_y(polyfixvecl *y1, polyfixveck *y2,int fm){
  if (fm==FM_SKIP||fm==FM_ZERO){ memset(y1,0,sizeof(*y1)); memset(y2,0,sizeof(*y2)); }
  else if (fm==FM_LOOPABORT){ memset(y2,0,sizeof(*y2)); }   /* 저엔트로피 근사 */
  else if (fm==FM_BITFLIP){ int32_t*p=(int32_t*)y1; p[0]^=1; }
  else if (fm==FM_SETCONST){ int32_t*p=(int32_t*)y1; p[0]=0; }
  else { int32_t*p=(int32_t*)y1; p[0]+=1; } }
static void fi_fault_b(uint8_t *b,int fm){
  if (fm==FM_BITFLIP) *b^=1;
  else if (fm==FM_SKIP||fm==FM_ZERO) *b&=~1u;
  else if (fm==FM_SETCONST) *b|=1u;
  else *b^=1; }
static void fi_corrupt_i32(int32_t *p,int fm){
  if (fm==FM_ZERO||fm==FM_SKIP) *p=0;
  else if (fm==FM_BITFLIP) *p^=1;
  else if (fm==FM_BYTEFLIP) ((uint8_t*)p)[0]^=0xFF;
  else if (fm==FM_SETCONST) *p=12345;
  else *p+=1; }
static void fi_fault_poly(poly *c,int fm){
  if (fm==FM_ZERO||fm==FM_SKIP) c->coeffs[0]=0;
  else if (fm==FM_BITFLIP) c->coeffs[0]^=1;
  else if (fm==FM_SETCONST) c->coeffs[0]=1;
  else if (fm==FM_BYTEFLIP) ((uint8_t*)c->coeffs)[0]^=0xFF;
  else c->coeffs[0]+=1; }

int sign_fi(uint8_t *sig, size_t *siglen,
                                   const uint8_t *m, size_t mlen,
                                   const uint8_t *pre, size_t prelen,
                                   const uint8_t rnd[HAETAE_SEEDBYTES],
                                   const uint8_t *sk) {

  uint8_t buf[HAETAE_POLYVECK_HIGHBITS_PACKEDBYTES + HAETAE_POLYC_PACKEDBYTES] =
      {0};
  uint8_t seedbuf[HAETAE_CRHBYTES] = {0}, key[HAETAE_SEEDBYTES] = {0};
  uint8_t mu[HAETAE_CRHBYTES] = {0};
  uint8_t b = 0; // one bit
  uint16_t counter = 0;
  uint64_t reject1, reject2;

  polyvecm s1;
  polyvecl A1[HAETAE_K], cs1;
  polyveck s2, cs2, highbits, Ay;
  polyfixvecl y1, z1, z1tmp;
  polyfixveck y2, z2, z2tmp;
  polyvecl z1rnd; // round of z1
  polyvecl hb_z1, lb_z1;
  polyveck z2rnd, h, htmp; // round of z2
  poly c, chat, z1rnd0, lsb;

  xof256_state state;

  unsigned int i;

  // Unpack secret key
  unpack_sk(A1, &s1, &s2, key, sk);
  /* FI: persistent key-memory fault (before NTT) */
  if (g_fp==FP_KEYMEM) fi_corrupt_polyvecm(&s1, g_fm);
  if (g_fp==FP_UNPACKA) fi_corrupt_i32(&A1[0].vec[0].coeffs[0], g_fm);
  { uint32_t ck=fi_polyvecm_ck(&s1);
    if (!g_have_golden_ck && g_fp==FP_NONE){ g_golden_ck=ck; g_have_golden_ck=1; }
    g_cur_ck=ck; }


  xof256_absorb_thrice(&state, sk, HAETAE_CRYPTO_PUBLICKEYBYTES, pre, prelen, m,
                       mlen);
  xof256_squeeze(mu, HAETAE_CRHBYTES, &state);

  xof256_absorb_thrice(&state, key, HAETAE_SEEDBYTES, rnd, HAETAE_SEEDBYTES, mu,
                       HAETAE_CRHBYTES);
  xof256_squeeze(seedbuf, HAETAE_CRHBYTES, &state);
  /* FI: sampling-seed fault */
  if (g_fp==FP_SEED) fi_fault_buf(seedbuf, HAETAE_CRHBYTES, g_fm);
  /* Lee-Ha sanity check: XOF 버퍼 all-zero/all-same 탐지 */
  if (g_cm==CM_LEEHA && fi_buf_degenerate(seedbuf, HAETAE_CRHBYTES)) g_leeha_detected=1;
  /* Lee-Ha partial-double: 시드 독립 재유도 후 비교 */
  if (g_cm==CM_LEEHA){ uint8_t sb2[HAETAE_CRHBYTES]; xof256_state st2;
    xof256_absorb_thrice(&st2,key,HAETAE_SEEDBYTES,rnd,HAETAE_SEEDBYTES,mu,HAETAE_CRHBYTES);
    xof256_squeeze(sb2,HAETAE_CRHBYTES,&st2);
    if(memcmp(sb2,seedbuf,HAETAE_CRHBYTES)) g_leeha_detected=1; }


  polyvecm_ntt(&s1);
  polyveck_ntt(&s2);

reject:
  if (++g_iter > FI_MAX_ITER) return 2;  /* FI: avoid infinite reject loop */

  /*------------------ 1. Sample y1 and y2 from hyperball ------------------*/
  uint16_t cb_lh = counter;
  counter = polyfixveclk_sample_hyperball(&y1, &y2, &b, seedbuf, counter);
  if (g_fp==FP_Y)       fi_fault_y(&y1, &y2, g_fm);
  if (g_fp==FP_SIGNBIT) fi_fault_b(&b, g_fm);
  /* Lee-Ha partial-double: 부호비트/난수 샘플 재계산 후 비교 */
  if (g_cm==CM_LEEHA){ polyfixvecl y1b; polyfixveck y2b; uint8_t bb=0;
    polyfixveclk_sample_hyperball(&y1b,&y2b,&bb,seedbuf,cb_lh);
    if(bb!=b || memcmp(&y1b,&y1,sizeof(y1)) || memcmp(&y2b,&y2,sizeof(y2))) g_leeha_detected=1; }


  /*------------------- 2. Compute a chanllenge c --------------------------*/
  // Round y1 and y2
  polyfixvecl_round(&z1rnd, &y1);
  polyfixveck_round(&z2rnd, &y2);

  // A * round(y) mod q = A1 * round(y1) + 2 * round(y2) mod q
  z1rnd0 = z1rnd.vec[0];
  polyvecl_ntt(&z1rnd);
  polymatkl_pointwise_montgomery(&Ay, A1, &z1rnd);
  polyveck_invntt_tomont(&Ay);
  polyveck_double(&z2rnd);
  polyveck_add(&Ay, &Ay, &z2rnd);
  if (g_fp==FP_COMMIT) fi_corrupt_i32(&Ay.vec[0].coeffs[0], g_fm);

  // recover A * round(y) mod 2q
  polyveck_poly_fromcrt(&Ay, &Ay, &z1rnd0);
  polyveck_freeze2q(&Ay);

  // HighBits of (A * round(y) mod 2q)
  polyveck_highbits_hint(&highbits, &Ay);

  // LSB(round(y_0) * j)
  poly_lsb(&lsb, &z1rnd0);
  if (g_fp==FP_LSB) fi_corrupt_i32(&lsb.coeffs[0], g_fm);

  // Pack HighBits of A * round(y) mod 2q and LSB of round(y0)
  pack_vec_highbits(buf, &highbits);
  pack_poly_lsb(buf + HAETAE_POLYVECK_HIGHBITS_PACKEDBYTES, &lsb);

  // c = challenge(highbits, lsb, mu)
  poly_challenge(&c, buf, mu);
  if (g_fp==FP_CHALLENGE) fi_fault_poly(&c, g_fm);


  /*------------------- 3. Compute z = y + (-1)^b c * s --------------------*/
  // cs = c * s = c * (si1 || s2)
  cs1.vec[0] = c;
  chat = c;
  poly_ntt(&chat);

  for (i = 1; i < HAETAE_L; ++i) {
    if (g_fp==FP_CS1 && (g_fm==FM_SKIP || g_fm==FM_ZERO)) {        /* T1: skip c*s1 */
      for (int k=0;k<HAETAE_N;k++) cs1.vec[i].coeffs[k]=0; continue; }
    if (g_fp==FP_CS1 && g_fm==FM_LOOPABORT) {                      /* T1: loop-abort */
      for (unsigned int j=i;j<HAETAE_L;j++) for(int k=0;k<HAETAE_N;k++) cs1.vec[j].coeffs[k]=0; break; }
    poly_pointwise_montgomery(&cs1.vec[i], &chat, &s1.vec[i - 1]);
    poly_invntt_tomont(&cs1.vec[i]);
    if (g_fp==FP_CS1 && g_fm==FM_BITFLIP) cs1.vec[i].coeffs[0]^=1;
    if (g_fp==FP_CS1 && g_fm==FM_SETCONST) cs1.vec[i].coeffs[0]=12345;
  }
  polyveck_poly_pointwise_montgomery(&cs2, &s2, &chat);
  polyveck_invntt_tomont(&cs2);

  // z = y + (-1)^b cs = z1 + z2
  polyvecl_cneg(&cs1, b & 1);
  polyveck_cneg(&cs2, b & 1);
  if (g_fp==FP_ADDY && (g_fm==FM_SKIP || g_fm==FM_ZERO)) {       /* T2: skip +y -> z1=LN*cs1 */
    polyfixvecl yzero; memset(&yzero, 0, sizeof(yzero));
    polyfixvecl_add(&z1, &yzero, &cs1);                          /* real y1 유지(IRV용) */
  } else {
    polyfixvecl_add(&z1, &y1, &cs1);
    if (g_fp==FP_ADDY && g_fm==FM_BITFLIP) z1.vec[0].coeffs[0]^=1;
  }
  polyfixveck_add(&z2, &y2, &cs2);

  // reject if norm(z) >= B'
  reject1 = ((uint64_t)HAETAE_B1SQ * HAETAE_LN * HAETAE_LN -
             polyfixveclk_sqnorm2(&z1, &z2)) >>
            63;
  reject1 &= 1;

  polyfixvecl_double(&z1tmp, &z1);
  polyfixveck_double(&z2tmp, &z2);

  polyfixfixvecl_sub(&z1tmp, &z1tmp, &y1);
  polyfixfixveck_sub(&z2tmp, &z2tmp, &y2);

  // reject if norm(2z-y) < B and b' = 0
  reject2 = (polyfixveclk_sqnorm2(&z1tmp, &z2tmp) -
             (uint64_t)HAETAE_B0SQ * HAETAE_LN * HAETAE_LN) >>
            63;
  reject2 &= 1;
  reject2 &= (b & 0x2) >> 1;

  if (g_fp==FP_REJECT && g_fm==FM_SKIP) { reject1=0; reject2=0; }  /* RB: skip rejection */

  if (reject1 | reject2) {
    goto reject;
  }

  /* ===== HAETAE-IRV: 무결성 검증(accept된 z에 대해) ===== */
  if (g_cm==CM_IRV) {
    int delta=0;
    /* M1: c*s1 재계산 -> z1 관계 재검증 */
    polyvecl cs1b; poly chatb=c; poly_ntt(&chatb);
    cs1b.vec[0]=c;
    for (unsigned int ii=1; ii<HAETAE_L; ++ii){
      poly_pointwise_montgomery(&cs1b.vec[ii],&chatb,&s1.vec[ii-1]);
      poly_invntt_tomont(&cs1b.vec[ii]); }
    polyvecl_cneg(&cs1b, b&1);
    polyfixvecl z1b; polyfixvecl_add(&z1b, &y1, &cs1b);
    for (unsigned int ii=0; ii<HAETAE_L && !delta; ++ii)
      for (int k=0;k<HAETAE_N;k++) if (z1.vec[ii].coeffs[k]!=z1b.vec[ii].coeffs[k]){delta=1;break;}
    /* M2: 서명경계 B1 독립 재검사(거부우회 탐지) */
    { uint64_t r=((uint64_t)HAETAE_B1SQ*HAETAE_LN*HAETAE_LN - polyfixveclk_sqnorm2(&z1,&z2))>>63;
      if (r & 1) delta=1; }
    /* M3: 비밀키 체크섬(영속 변조 탐지) */
    if (g_have_golden_ck && g_cur_ck!=g_golden_ck) delta=1;
    if (delta) g_irv_detected=1;   /* 무분기 감염: 출력 무효화(여기선 탐지 플래그) */
  }

  /*------------------- 4. Make a hint -------------------------------------*/
  // Round z1 and z2
  polyfixvecl_round(&z1rnd, &z1);
  polyfixveck_round(&z2rnd, &z2);

  // recover A1 * round(z1) - qcj mod 2q
  polyveck_double(&z2rnd);
  polyveck_sub(&htmp, &Ay, &z2rnd);
  polyveck_freeze2q(&htmp);

  // HighBits of (A * round(z) - qcj mod 2q) and (A1 * round(z1) - qcj mod 2q)
  polyveck_highbits_hint(&htmp, &htmp);
  polyveck_sub(&h, &highbits, &htmp);
  polyveck_caddDQ2ALPHA(&h);
  if (g_fp==FP_HINT) fi_corrupt_i32(&h.vec[0].coeffs[0], g_fm);

  /*------------------ Decompose(z1) and Pack signature -------------------*/
  polyvecl_lowbits(&lb_z1, &z1rnd); // TODO do this in one function together!
  polyvecl_highbits(&hb_z1, &z1rnd);

  if (pack_sig(sig, &c, &lb_z1, &hb_z1,
               &h)) { // reject if signature is too big
    goto reject;
  }
  *siglen = HAETAE_CRYPTO_BYTES;

  return 0;
}


