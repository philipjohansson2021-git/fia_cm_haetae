// SPDX-License-Identifier: MIT
// ChipWhisperer STM32F4 main — HAETAE 전체 서명 결함주입 타겟 (VARIANT: baseline/double/leeha/irv).
//
// 커맨드 (SimpleSerial v1.1):
//   'k' (0B)  : 결정론 키쌍 재생성(재현성)         → 'r' 1B (=0)
//   'p' (16B) : 1회 서명(+표적 구간 트리거)         → 'r' 16B = 서명의 SHAKE256 다이제스트
//   'z' (1B)  : 마지막 서명 g_sig 를 64B 청크 스트리밍 → 'r' 64B  (호스트 키복구/검증용)
//   't' (16B) : 1회 서명 사이클수(DWT) 측정          → 'r' 4B  = CYCCNT (오버헤드 측정용)
//
// RNG: 고정 시드 DRBG. 키생성 전 randombytes_reset() 으로 4개 변형이 동일 키·동일 nonce 사용
//      → baseline 과 대응기법을 1:1 로 대조. 서명 nonce(rnd)는 고정값 0x07.
#include "hal.h"
#include "simpleserial.h"
#include "api.h"
#include "fips202.h"
#include "fault_sim.h"
#include <stdint.h>
#include <string.h>

extern int haetae_sign_cm(uint8_t*, size_t*, const uint8_t*, size_t,
                          const uint8_t*, size_t, const uint8_t*, const uint8_t*);
void randombytes_reset(void);

static uint8_t pk[CRYPTO_PUBLICKEYBYTES], sk[CRYPTO_SECRETKEYBYTES];
static uint8_t g_sig[CRYPTO_BYTES];
static size_t  g_slen;
static uint8_t g_msg[16] = {0};     // 서명할 메시지(가변). 'p' 입력으로 갱신 → y 다양화(성공률 측정)
static uint8_t PRE[1] = {0};
static int keys_ready = 0;          // keypair 지연 생성 플래그(부팅 행 방지: 통신 먼저)

static void ensure_keys(void){      // 첫 서명/키요청 시점에 결정론 키 생성
    if (!keys_ready){ randombytes_reset(); crypto_sign_keypair(pk, sk); keys_ready = 1; }
}

// DWT 사이클 카운터(Cortex-M4) — 무결함 서명 1회의 사이클수 측정(오버헤드 표).
static inline void dwt_init(void){
  volatile uint32_t *DEMCR = (uint32_t*)0xE000EDFCu;
  volatile uint32_t *CTRL  = (uint32_t*)0xE0001000u;
  *DEMCR |= (1u << 24);   // TRCENA
  *CTRL  |= 1u;           // CYCCNTENA
}
static inline uint32_t dwt_cyccnt(void){ return *(volatile uint32_t*)0xE0001004u; }

// 한 번 서명 + 변형별 후처리(double=2회비교, leeha=서명후검증). 결함 탐지 시 출력 무효화.
static void do_sign(void){
  ensure_keys();                                             // 지연 키 생성
  uint8_t rnd[HAETAE_SEEDBYTES];
  for (int i = 0; i < HAETAE_SEEDBYTES; i++) rnd[i] = 0x07;   // 결정론(실험용)
  g_slen = 0;
#ifdef HAETAE_VARIANT_DOUBLE
  uint8_t s2[CRYPTO_BYTES]; size_t l2 = 0;                       // 전체 이중연산
  haetae_sign_cm(g_sig, &g_slen, g_msg, 16, PRE, 1, rnd, sk);    // 1차 (SW결함 주입 시 여기 적용)
#ifdef FAULT_SIM
  int _fl = g_fault_line; g_fault_line = 0;                      // 단일 transient 모델: 2차는 무결함
#endif
  haetae_sign_cm(s2,    &l2,     g_msg, 16, PRE, 1, rnd, sk);    // 2차 (무결함 재계산)
#ifdef FAULT_SIM
  g_fault_line = _fl;
#endif
  { int mism = (g_slen != l2 || memcmp(g_sig, s2, g_slen));   // 비교(탐지-후-중단)
#ifdef FAULT_SIM
    if (g_fault_checkskip) mism = 0;                          // 2차 결함: 비교/중단 분기 스킵 → 우회
#endif
    if (mism) memset(g_sig, 0xFF, CRYPTO_BYTES); }            // 불일치→무효화
#else
  haetae_sign_cm(g_sig, &g_slen, g_msg, 16, PRE, 1, rnd, sk);
#endif
#ifdef HAETAE_VARIANT_LEEHA
  { int bad = crypto_sign_verify(g_sig, g_slen, g_msg, 16, PRE, 0, pk); // 서명후검증(탐지-후-중단)
#ifdef FAULT_SIM
    if (g_fault_checkskip) bad = 0;                           // 2차 결함: 검증/중단 분기 스킵 → 우회
#endif
    if (bad) memset(g_sig, 0xFF, CRYPTO_BYTES); }
#endif
#ifdef HAETAE_VARIANT_IRV
  /* M1'(상류 결함 보강): 서명 밖에서 표준검증 → LSB/UNPACK 등 "유효하지 않은 서명" 포착.
     응답연산 핵심(T1/T2/RB)은 이미 서명 내부 무분기 감염이 처리(여기 분기와 무관). */
  { int bad = crypto_sign_verify(g_sig, g_slen, g_msg, 16, PRE, 0, pk);
#ifdef FAULT_SIM
    if (g_fault_checkskip) bad = 0;
#endif
    if (bad) memset(g_sig, 0xFF, CRYPTO_BYTES); }
#endif
}

// 'e' (0B): 순수 통신 테스트(암호 연산 없음) → 'r' 16B = 0xA0..0xAF. 통신/클럭 분리 진단용.
uint8_t cmd_echo(uint8_t *in, uint8_t len){ (void)in; (void)len;
    uint8_t e[16]; for (int i = 0; i < 16; i++) e[i] = (uint8_t)(0xA0 + i);
    simpleserial_put('r', 16, e); return 0x00; }

uint8_t cmd_keygen(uint8_t *in, uint8_t len){ (void)in; (void)len;
    keys_ready = 0; ensure_keys();                  // 강제 재생성
    simpleserial_put('r', 1, (uint8_t[]){0}); return 0x00; }

uint8_t cmd_sign(uint8_t *in, uint8_t len){ (void)len;
    memcpy(g_msg, in, 16);                                  // 입력 16B를 메시지로 → y 다양화
    do_sign();
    uint8_t dig[16]; shake256(dig, 16, g_sig, g_slen ? g_slen : CRYPTO_BYTES);
    simpleserial_put('r', 16, dig); return 0x00; }

uint8_t cmd_zread(uint8_t *in, uint8_t len){ (void)len;
    uint16_t idx = (uint16_t)(in[0] & 0xFF) * 64u; uint8_t out[64];
    for (int i = 0; i < 64; i++) out[i] = (idx + i < CRYPTO_BYTES) ? g_sig[idx + i] : 0;
    simpleserial_put('r', 64, out); return 0x00; }

uint8_t cmd_cycles(uint8_t *in, uint8_t len){ (void)in; (void)len;
    dwt_init();
    uint32_t t0 = dwt_cyccnt();
    do_sign();
    uint32_t cyc = dwt_cyccnt() - t0;
    uint8_t b[4]; for (int i = 0; i < 4; i++) b[i] = (uint8_t)(cyc >> (8*i));
    simpleserial_put('r', 4, b); return 0x00; }

#ifdef FAULT_SIM
extern int32_t g_z1raw[];   // 결함 응답 z1 (1024 int32 = 4096B = 64청크)
extern int32_t g_s1ntt[];   // 참 s1(NTT)   ( 768 int32 = 3072B = 48청크)
extern int32_t g_cpoly[];   // 챌린지 c     ( 256 int32 = 1024B = 16청크)
// 'f' (3B = [라인 ID, one-shot, check-skip]): 결함 라인 + 모드 + 2차결함(탐지분기 스킵)
uint8_t cmd_fault(uint8_t *in, uint8_t len){ (void)len;
    g_fault_line = in[0]; g_fault_oneshot = in[1]; g_fault_checkskip = in[2];
    simpleserial_put('r', 1, (uint8_t[]){(uint8_t)g_fault_line}); return 0x00; }
// 직접 추출 검증용 64B 청크 스트리밍 ('x'=z1raw, 's'=s1ntt, 'c'=challenge)
uint8_t cmd_z1raw(uint8_t *in, uint8_t len){ (void)len;
    simpleserial_put('r', 64, ((uint8_t*)g_z1raw) + ((in[0] & 0x3F) * 64)); return 0x00; }
uint8_t cmd_s1ntt(uint8_t *in, uint8_t len){ (void)len;
    simpleserial_put('r', 64, ((uint8_t*)g_s1ntt) + ((in[0] & 0x3F) * 64)); return 0x00; }
uint8_t cmd_cpoly(uint8_t *in, uint8_t len){ (void)len;
    simpleserial_put('r', 64, ((uint8_t*)g_cpoly) + ((in[0] & 0x0F) * 64)); return 0x00; }
#endif

int main(void){
    platform_init(); init_uart(); trigger_setup();
    simpleserial_init();                                       // 통신 먼저(키생성은 지연)
    simpleserial_addcmd('e', 0,  cmd_echo);                    // 순수 통신 진단
    simpleserial_addcmd('k', 0,  cmd_keygen);
    simpleserial_addcmd('p', 16, cmd_sign);
    simpleserial_addcmd('z', 1,  cmd_zread);
    simpleserial_addcmd('t', 16, cmd_cycles);
#ifdef FAULT_SIM
    simpleserial_addcmd('f', 3,  cmd_fault);   // [라인, one-shot, check-skip] SW 결함 선택 (축 B)
    simpleserial_addcmd('x', 1,  cmd_z1raw);   // 결함 응답 z1 스트리밍
    simpleserial_addcmd('s', 1,  cmd_s1ntt);   // 참 s1(NTT) 스트리밍
    simpleserial_addcmd('c', 1,  cmd_cpoly);   // 챌린지 c 스트리밍
#endif
    while(1) simpleserial_get();
}
