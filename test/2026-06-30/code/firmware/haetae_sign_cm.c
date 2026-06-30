// SPDX-License-Identifier: MIT
// haetae_sign_cm.c — HAETAE 전체 서명 + 대응기법(VARIANT) + CW 트리거. STM32F4 타겟.
//
//   * 결함은 "하드웨어 클럭 글리치"가 만든다 → 소프트웨어 결함 훅 없음(깨끗한 서명).
//   * 표적 연산 구간 z = y + (-1)^b c*s (c*s 곱셈 ~ +y 덧셈, T1/T2)에
//     trigger_high()/trigger_low() 를 둔다.
//   * 대응기법은 컴파일타임 매크로로 선택(makefile VARIANT):
//       (없음)                 = baseline (무방어, 레퍼런스 서명 그대로)
//       -DHAETAE_VARIANT_IRV   = HAETAE-IRV (M1 c*s 재계산 + M2 B1 노름 재검사
//                                + M3 sk 체크섬 + M4 무분기 감염 마스킹)
//       -DHAETAE_VARIANT_LEEHA = Lee-Ha (※ 실제 논문 스펙으로 교체 예정 — 현재는 임시 골격)
//       -DHAETAE_VARIANT_DOUBLE= 전체 이중연산 (main 에서 2회 호출·비교; 본 파일은 baseline 동일)
//   * 대응이 결함을 탐지하면(잔차 cm_delta != 0) 출력 서명을 PRF로 난수화(감염)하여
//     키유출을 차단한다(무분기). baseline/double 빌드에서는 이 코드가 전부 #ifdef 로 제거됨.
//   * 레퍼런스 crypto_sign_signature_internal 과 산술적으로 동일(같은 rnd/sk → 동일 서명).
#include "api.h"
#include "packing.h"
#include "params.h"
#include "poly.h"
#include "polyfix.h"
#include "polymat.h"
#include "polyvec.h"
#include "randombytes.h"
#include "symmetric.h"
#ifdef CW_TARGET
#include "hal.h"               // trigger_high()/trigger_low()
#else
#define trigger_high()         // x86 sanity 빌드용 스텁
#define trigger_low()
#endif
#include "fips202.h"
#include "fault_sim.h"           // 축 B: SW 라인별 결함주입 ID (FL_*) — FAULT_SIM 빌드 전용
#include <stdint.h>
#include <string.h>

#ifdef FAULT_SIM
volatile int g_fault_line = 0;   // 호스트 'f' 가 설정하는 결함 라인 ID(FL_*); 0=무결함
volatile int g_fault_oneshot = 0;// 0=persistent, 1=one-shot(단일 transient: 첫 발생만 주입)
volatile int g_fault_checkskip = 0; // 1=2차 결함(대응기법 탐지-후-중단 분기 스킵; main에서 사용)
static int g_fault_armed = 0;    // one-shot 무장(서명 진입 시 1, 첫 발생에서 소비)
// 결함 발사 판정: persistent면 항상, one-shot이면 무장 상태일 때 1회만.
static inline int fault_fire(int line){
  if (g_fault_line != line) return 0;
  if (!g_fault_oneshot)     return 1;     // persistent: 매 발생
  if (!g_fault_armed)       return 0;     // one-shot: 이미 소비됨
  g_fault_armed = 0; return 1;            // one-shot: 첫 발생 소비
}
// 직접 추출 실험용 덤프(공격자 관점 아님, 복원 검증용): 결함 응답 z1·참 s1(NTT)·챌린지 c
int32_t g_z1raw[HAETAE_L * HAETAE_N];   // 채택된 응답 z1 의 원시 정수계수 (T2: = LN*cs1)
int32_t g_s1ntt[HAETAE_M * HAETAE_N];   // 서명에 쓰인 참 s1(NTT 도메인) — 복원 일치율 검증
int32_t g_cpoly[HAETAE_N];              // 채택된 챌린지 c 계수 — 복원식의 ĉ 계산용
#endif

// 결함으로 거부루프가 폭주할 때의 안전 상한(무한루프 방지). 정상 서명은 보통 수~수십 회.
#define FI_MAX_ITER 4000

#if defined(HAETAE_VARIANT_IRV) || defined(HAETAE_VARIANT_LEEHA)
static uint32_t g_golden_ck = 0; static int g_have_ck = 0;
// 비밀키 s1(NTT 전) 영역의 FNV-1a 체크섬 — 영속 키 변조(M3) 탐지용.
static uint32_t ck_polyvecm(const polyvecm *s){
  uint32_t h = 2166136261u; const int32_t *p = (const int32_t*)s;
  for (size_t i = 0; i < sizeof(polyvecm)/4; i++){ h ^= (uint32_t)p[i]; h *= 16777619u; }
  return h;
}
// 무분기 감염형 마스킹: cm_delta != 0 이면 비밀시드+delta 로 만든 PRF 스트림으로 서명을
// 통째로 난수화(XOR) → 검증 실패 + 키정보 0. cm_delta == 0 이면 factor==0 이라 불변.
static void infect_sig(uint8_t *sig, uint64_t delta, const uint8_t *sk){
  uint8_t factor = (uint8_t)(0u - (uint8_t)((delta | (0u - delta)) >> 63)); // delta!=0 -> 0xFF
  uint8_t seed[HAETAE_SEEDBYTES + 8]; uint8_t ks[HAETAE_CRYPTO_BYTES];
  for (int i = 0; i < HAETAE_SEEDBYTES; i++)                  // sk 끝의 비밀 시드(key)로 키잉
    seed[i] = sk[HAETAE_CRYPTO_SECRETKEYBYTES - HAETAE_SEEDBYTES + i];
  for (int i = 0; i < 8; i++) seed[HAETAE_SEEDBYTES + i] = (uint8_t)(delta >> (8*i));
  shake256(ks, HAETAE_CRYPTO_BYTES, seed, HAETAE_SEEDBYTES + 8);
  for (size_t i = 0; i < HAETAE_CRYPTO_BYTES; i++) sig[i] ^= (uint8_t)(ks[i] & factor);
}
#endif

int haetae_sign_cm(uint8_t *sig, size_t *siglen,
                   const uint8_t *m, size_t mlen,
                   const uint8_t *pre, size_t prelen,
                   const uint8_t rnd[HAETAE_SEEDBYTES], const uint8_t *sk) {
  uint8_t buf[HAETAE_POLYVECK_HIGHBITS_PACKEDBYTES + HAETAE_POLYC_PACKEDBYTES] = {0};
  uint8_t seedbuf[HAETAE_CRHBYTES] = {0}, key[HAETAE_SEEDBYTES] = {0};
  uint8_t mu[HAETAE_CRHBYTES] = {0};
  uint8_t b = 0;
  uint16_t counter = 0;
  uint64_t reject1, reject2;
  int g_iter = 0;
#if defined(HAETAE_VARIANT_IRV) || defined(HAETAE_VARIANT_LEEHA)
  uint64_t cm_delta = 0;       // 대응 탐지 잔차(0이면 무결함)
#endif

  polyvecm s1;
  polyvecl A1[HAETAE_K], cs1;
  polyveck s2, cs2, highbits, Ay;
  polyfixvecl y1, z1, z1tmp;
  polyfixveck y2, z2, z2tmp;
  polyvecl z1rnd, hb_z1, lb_z1;
  polyveck z2rnd, h, htmp;
  poly c, chat, z1rnd0, lsb;
  xof256_state state;
  unsigned int i;

#ifdef FAULT_SIM
  g_fault_armed = (g_fault_line != 0);   // 이 서명 1회에 대한 one-shot 무장
#endif

  // 비밀키 언팩
  unpack_sk(A1, &s1, &s2, key, sk);
#ifdef FAULT_SIM
  if (fault_fire(FL_UNPACK)) memset(&A1[0], 0, sizeof(polyvecl)); // 공개행렬 A 언패킹 변조
#endif

#if defined(HAETAE_VARIANT_IRV) || defined(HAETAE_VARIANT_LEEHA)
  { uint32_t ck = ck_polyvecm(&s1);
    if (!g_have_ck){ g_golden_ck = ck; g_have_ck = 1; }   // 기준 체크섬(첫 무결함 서명)
    if (ck != g_golden_ck) cm_delta |= 1;                 // M3: 비밀키 영속 변조 탐지
  }
#endif

  xof256_absorb_thrice(&state, sk, HAETAE_CRYPTO_PUBLICKEYBYTES, pre, prelen, m, mlen);
  xof256_squeeze(mu, HAETAE_CRHBYTES, &state);
  xof256_absorb_thrice(&state, key, HAETAE_SEEDBYTES, rnd, HAETAE_SEEDBYTES, mu, HAETAE_CRHBYTES);
  xof256_squeeze(seedbuf, HAETAE_CRHBYTES, &state);
#ifdef FAULT_SIM
  if (fault_fire(FL_SEED)) memset(seedbuf, 0, HAETAE_CRHBYTES); // 시드 squeeze 스킵 → 0 고정
#endif

#ifdef HAETAE_VARIANT_LEEHA
  /* TODO(Lee-Ha): 실제 논문 스펙으로 교체. 현재는 컴파일/스모크용 임시 골격
     (시드 비정상성 검사 + 시드 독립 재유도 비교). */
  { int allz = 1;
    for (size_t t = 0; t < HAETAE_CRHBYTES; t++) if (seedbuf[t]) { allz = 0; break; }
    if (allz) cm_delta |= 1;
    uint8_t sb2[HAETAE_CRHBYTES]; xof256_state st2;
    xof256_absorb_thrice(&st2, key, HAETAE_SEEDBYTES, rnd, HAETAE_SEEDBYTES, mu, HAETAE_CRHBYTES);
    xof256_squeeze(sb2, HAETAE_CRHBYTES, &st2);
    if (memcmp(sb2, seedbuf, HAETAE_CRHBYTES)) cm_delta |= 1;
  }
#endif

  polyvecm_ntt(&s1);
  polyveck_ntt(&s2);
#ifdef FAULT_SIM
  memcpy(g_s1ntt, &s1, sizeof(g_s1ntt));   // 참 s1(NTT) 덤프 (복원 검증 ground-truth)
#endif

reject:
  if (++g_iter > FI_MAX_ITER) return 2;                    // 결함 폭주 안전탈출

  /* 1. 하이퍼볼에서 y1, y2 샘플 */
  uint16_t cb = counter;
  counter = polyfixveclk_sample_hyperball(&y1, &y2, &b, seedbuf, counter);
#ifdef FAULT_SIM
  if (fault_fire(FL_SIGNBIT)) b ^= 1;   // bimodal 부호 비트 반전
#endif

  (void)cb;   /* Lee-Ha 부분 이중연산은 거부 통과 후 1회만 수행(공정 비용) → 아래 post-reject 블록 */

  /* 2. 챌린지 c 계산 */
  polyfixvecl_round(&z1rnd, &y1);
  polyfixveck_round(&z2rnd, &y2);
  z1rnd0 = z1rnd.vec[0];
  polyvecl_ntt(&z1rnd);
  polymatkl_pointwise_montgomery(&Ay, A1, &z1rnd);
  polyveck_invntt_tomont(&Ay);
  polyveck_double(&z2rnd);
  polyveck_add(&Ay, &Ay, &z2rnd);
  polyveck_poly_fromcrt(&Ay, &Ay, &z1rnd0);
  polyveck_freeze2q(&Ay);
  polyveck_highbits_hint(&highbits, &Ay);
  poly_lsb(&lsb, &z1rnd0);
#ifdef FAULT_SIM
  if (fault_fire(FL_LSB)) memset(&lsb, 0, sizeof(poly));   // LSB 추출 스킵 → 다른 c
#endif
  pack_vec_highbits(buf, &highbits);
  pack_poly_lsb(buf + HAETAE_POLYVECK_HIGHBITS_PACKEDBYTES, &lsb);
  poly_challenge(&c, buf, mu);

  /* 3. z = y + (-1)^b c*s   === 표적 연산 구간(T1: c*s 스킵, T2: +y 스킵) === */
  trigger_high();
  cs1.vec[0] = c;
  chat = c;
  poly_ntt(&chat);
  for (i = 1; i < HAETAE_L; ++i) {
    poly_pointwise_montgomery(&cs1.vec[i], &chat, &s1.vec[i - 1]);
    poly_invntt_tomont(&cs1.vec[i]);
  }
  polyveck_poly_pointwise_montgomery(&cs2, &s2, &chat);
  polyveck_invntt_tomont(&cs2);
#ifdef FAULT_SIM
  if (fault_fire(FL_CS)) {                 // T1: c*s 곱셈 스킵 → cs≈0 → z≈y (nonce 유출)
    for (unsigned int ii = 1; ii < HAETAE_L; ++ii) memset(&cs1.vec[ii], 0, sizeof(poly));
    memset(&cs2, 0, sizeof(cs2));
  }
#endif
  polyvecl_cneg(&cs1, b & 1);
  polyveck_cneg(&cs2, b & 1);
#ifdef FAULT_SIM
  if (fault_fire(FL_ADDY)) {               // T2: +y 덧셈 스킵 → z=(-1)^b c*s (y 제거, s1 유출)
    polyfixvecl yz; memset(&yz, 0, sizeof(yz)); polyfixvecl_add(&z1, &yz, &cs1);
    polyfixveck wz; memset(&wz, 0, sizeof(wz)); polyfixveck_add(&z2, &wz, &cs2);
  } else
#endif
  { polyfixvecl_add(&z1, &y1, &cs1);
    polyfixveck_add(&z2, &y2, &cs2); }
  trigger_low();

  /* 4. 거부 샘플링(서명경계 B1 / 바이모달 B0) */
  reject1 = ((uint64_t)HAETAE_B1SQ * HAETAE_LN * HAETAE_LN - polyfixveclk_sqnorm2(&z1, &z2)) >> 63;
  reject1 &= 1;
  polyfixvecl_double(&z1tmp, &z1);
  polyfixveck_double(&z2tmp, &z2);
  polyfixfixvecl_sub(&z1tmp, &z1tmp, &y1);
  polyfixfixveck_sub(&z2tmp, &z2tmp, &y2);
  reject2 = (polyfixveclk_sqnorm2(&z1tmp, &z2tmp) - (uint64_t)HAETAE_B0SQ * HAETAE_LN * HAETAE_LN) >> 63;
  reject2 &= 1;
  reject2 &= (b & 0x2) >> 1;
#ifdef FAULT_SIM
  if (!fault_fire(FL_REJECT))                  // RB: 거부 판정 스킵 → 경계초과 z 방출
#endif
  if (reject1 | reject2) goto reject;

#ifdef FAULT_SIM
  memcpy(g_z1raw, &z1, sizeof(g_z1raw));       // 채택된 응답 z1 원시값 (T2: = LN*cs1)
  memcpy(g_cpoly, &c,  sizeof(g_cpoly));       // 채택된 챌린지 c
#endif

#ifdef HAETAE_VARIANT_IRV
  /* HAETAE-IRV: z 확정 직후 무결성 검증 (잔차 cm_delta 누적) */
  { polyvecl cs1b; poly chatb = c; poly_ntt(&chatb);
    cs1b.vec[0] = c;
    for (unsigned int ii = 1; ii < HAETAE_L; ++ii){
      poly_pointwise_montgomery(&cs1b.vec[ii], &chatb, &s1.vec[ii-1]);
      poly_invntt_tomont(&cs1b.vec[ii]); }
    polyvecl_cneg(&cs1b, b & 1);
    polyfixvecl z1b; polyfixvecl_add(&z1b, &y1, &cs1b);
    for (unsigned int ii = 0; ii < HAETAE_L; ++ii)            // M1: z1 == y1+(-1)^b c*s1' ?
      for (int k = 0; k < HAETAE_N; k++)
        if (z1.vec[ii].coeffs[k] != z1b.vec[ii].coeffs[k]) cm_delta |= 1;
    /* M2: 서명경계 B1 + 바이모달 보조경계 B0 둘 다 재검사 (거부우회 RB 차단) */
    uint64_t r1 = ((uint64_t)HAETAE_B1SQ * HAETAE_LN * HAETAE_LN - polyfixveclk_sqnorm2(&z1, &z2)) >> 63;
    uint64_t r2 = (polyfixveclk_sqnorm2(&z1tmp, &z2tmp) - (uint64_t)HAETAE_B0SQ * HAETAE_LN * HAETAE_LN) >> 63;
    r2 &= (b & 0x2) >> 1;
    if ((r1 | r2) & 1) cm_delta |= 1;
    /* M1b: 시드 정상성 — 시드가 0/동일패턴이면 결함(시드 squeeze 스킵). */
    { int allz = 1, alls = 1;
      for (int t = 0; t < HAETAE_CRHBYTES; t++){ if (seedbuf[t]) allz = 0; if (seedbuf[t] != seedbuf[0]) alls = 0; }
      if (allz | alls) cm_delta |= 1; }
    /* M1c: 부호비트/논스 재유도(부분 이중연산) — 같은 시드·카운터로 재샘플해 b·y 대조.
       SIGNBIT(b 반전)는 부호 뒤집힌 서명도 유효해 검증/곱셈재계산으로 안 잡히므로 별도 포착. */
    { polyfixvecl y1b; polyfixveck y2b; uint8_t bb = 0;
      polyfixveclk_sample_hyperball(&y1b, &y2b, &bb, seedbuf, cb);
      if (bb != b || memcmp(&y1b, &y1, sizeof(y1)) || memcmp(&y2b, &y2, sizeof(y2))) cm_delta |= 1; }
  }
#endif

#ifdef HAETAE_VARIANT_LEEHA
  /* Lee-Ha 부분 이중연산: 채택된 시도에 대해 1회만 (시드/부호비트 재유도 비교).
     거부루프 매 반복이 아니라 통과 후 1회 → Lee-Ha 보고 오버헤드(+0.39%)에 부합. */
  { polyfixvecl y1b; polyfixveck y2b; uint8_t bb = 0;
    polyfixveclk_sample_hyperball(&y1b, &y2b, &bb, seedbuf, cb);
    if (bb != b || memcmp(&y1b, &y1, sizeof(y1)) || memcmp(&y2b, &y2, sizeof(y2))) cm_delta |= 1; }
#endif

  /* 5. 힌트 생성 */
  polyfixvecl_round(&z1rnd, &z1);
  polyfixveck_round(&z2rnd, &z2);
  polyveck_double(&z2rnd);
  polyveck_sub(&htmp, &Ay, &z2rnd);
  polyveck_freeze2q(&htmp);
  polyveck_highbits_hint(&htmp, &htmp);
  polyveck_sub(&h, &highbits, &htmp);
  polyveck_caddDQ2ALPHA(&h);

  /* 6. z1 분해 + 서명 패킹 */
  polyvecl_lowbits(&lb_z1, &z1rnd);
  polyvecl_highbits(&hb_z1, &z1rnd);
  if (pack_sig(sig, &c, &lb_z1, &hb_z1, &h)) goto reject;
  *siglen = HAETAE_CRYPTO_BYTES;

  /* 주: M1'(상류 결함 LSB/UNPACK용 표준검증)은 스택 절약을 위해 서명 함수 밖(main)에서 수행.
     내부에는 응답연산 핵심 검사(M1/M2/M1b/M1c)만 두어 무분기 감염으로 즉시 확산한다. */
#if defined(HAETAE_VARIANT_IRV) || defined(HAETAE_VARIANT_LEEHA)
  infect_sig(sig, cm_delta, sk);   // M4(무분기 감염): 결함이면 출력 난수화 → 키유출 0
#endif
  return 0;
}
