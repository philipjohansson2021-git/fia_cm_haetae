# T1 (c·s 스킵 → z=y) 클럭글리치 실험 — 펌웨어/빌드/노트북 안내

Husky + CW308_STM32F4 에서 **T1** 을 실행하기 위한 자료. T1 은 챌린지 곱 `c·s1` 을 스킵해
결함 응답을 `z1 = y1`(nonce) 로 만들고, 고정-nonce 로 얻은 깨끗한 응답
`z_clean = y1 + (-1)^b·LN·c·s1` 과의 **차분**으로 `s1` 을 복원한다.

성공 판정은 프록시가 아니라 **디바이스 참 s1 과 계수단위 정확 일치(768/768)**. 드라이버/복원:
`exp7_t1_driver.py`, `haetae_recover_t1.py` (기존 비트정확 `haetae_recover.py` 는 미수정 재사용).

---

## 두 개의 실행 축 (중요)

| 축 | 펌웨어 | 기대 결과 | 의미 |
|----|--------|-----------|------|
| **A. 저항 특성화** | **미수정** `haetae-baseline-FSIM-*.hex` | 대부분 `other` (T1_leak≈0) | 미수정 레퍼런스는 `cs1/cs2` 가 zero-init 이 아니라 c·s 스킵=쓰레기 → `diff%LN≠0` 게이트가 걸러냄. **"융합/미초기화가 물리 T1 을 막는다"** 는 결과. |
| **B. 클린 누설(인과 대조)** | EDIT 1(+EDIT 2) 적용 빌드 | 좁은 밴드에서 `T1_leak` | cs pre-zero 로 loop-abort→`z=y`. `s1` 계수단위 100% 복원. twopass 가 T2 의 인과 대조인 것과 동형. |

축 A 는 **지금 바로 실행 가능**(펌웨어 수정 불필요). 축 B 는 아래 EDIT 적용 후 재빌드.

---

## 노트북 사용법 (셀 순서)

```python
# [셀 1] EXP7-a 부트스트랩 실행 (scope/target/flash/recover_target/set_glitch/ss_trig/FL/SIGN_MS/WIN 정의)
#   단, TRIG_POINT 는 T1 을 위해 CS 로: 아래 한 줄을 EXP7-a 실행 후 추가 실행
TRIG_POINT = FL['CS']            # 트리거지점 = c·s (T1). 리셋 후 recover_target 가 이 값으로 재설정.
```
```python
# [셀 2] T1 드라이버 로드 (-i 필수)
%run -i exp7_t1_driver.py
```
```python
# [셀 3-A] 축 A: 저항 특성화 (미수정 FSIM 펌웨어에서 즉시)
run_t1_fullsign(hexname='haetae-baseline-FSIM-CW308_STM32F4.hex', N=400)
#   → golden/other/mute 위주, T1_leak≈0. "미수정 레퍼런스 물리 T1 저항" 데이터 + fig.
```
```python
# [셀 3-B] 축 B: 클린 누설 (EDIT 1+2 빌드 후)
run_t1_jig(hexname='haetae-JIG-T1-fused-CW308_STM32F4.hex', N=600)   # 동일 nonce 보장(fast)
verify_t1_leak(e, w, o, rep, K=30, path='jig')                       # 발견 파라미터 재현 + s값 정밀검증
#   또는 full-sign 로 교차검증:
run_t1_fullsign(hexname='haetae-baseline-FSIM-T1-CW308_STM32F4.hex', N=800)
```

판정 임계 `LEAK_TH_T1=0.999`. `T1_leak` = `diff` 가 LN 배수(ln_exact) **이고** 참 s1 과 768/768 일치.

---

## 펌웨어 EDIT (축 B 전용, 미수정 레퍼런스는 그대로 둠)

파일: `firmware/mcu/simpleserial-haetae/haetae_sign_cm.c`, `.../simpleserial-haetae.c`.
FL_CS 트리거(`TRIG_HI/LO(FL_CS)` at haetae_sign_cm.c:239/255)는 **이미 존재** → 새 트리거 불필요.

### EDIT 1 — c·s 스킵이 `z=y` 를 내도록 cs 사전 0화 (full-sign 경로, MANDATORY)
`haetae_sign_cm.c` 의 `TRIG_HI(FL_CS)`(239행) **바로 앞**에 삽입. 미수정 레퍼런스 보존을 위해
`T1_CS_ZEROINIT` 매크로로 감싼다(정의 안 하면 바이트동일).
```c
#ifdef T1_CS_ZEROINIT
  for (unsigned int ii = 1; ii < HAETAE_L; ++ii) memset(&cs1.vec[ii], 0, sizeof(poly));
  memset(&cs2, 0, sizeof(cs2));            /* 트리거 밖에서 0화 → 스킵 시 z=y (cs1.vec[0]=c 는 240행에서 재설정) */
#endif
  TRIG_HI(FL_CS);                          /* (기존 239행) */
```
효과: c·s 루프가 loop-abort 되면 `cs1.vec[1..3]=0, cs2=0` → `z1.vec[1..3]=y1.vec[1..3]`.
`cs1.vec[0]=c` 는 유지되므로 차분에서 block0 은 0 으로 상쇄(정상). **성공 판정은 `agreement`(정확일치)로**.

### EDIT 2 — fast-jig T1 재실행 경로 (동일 nonce 보장, 선택이지만 권장)
기존 `haetae_axisa_fire`(79–99행)는 **+y 만** 재실행 → T1 불가. c·s 를 재실행하는 fire 를 추가.

(1) 저장 상태 확장 — `haetae_sign_cm.c` 76–78행 근처(타입은 실제 `s1`(polyvecm)/`s2`(polyveck)에 맞춤):
```c
#ifdef AXISA_JIG
static polyvecm j_s1; static polyveck j_s2; static poly j_c; static uint8_t j_b;  // T1 재실행 입력
#endif
```
(2) prime 저장 블록(317–322행) 안에 추가:
```c
  memcpy(&j_s1, &s1, sizeof(j_s1)); memcpy(&j_s2, &s2, sizeof(j_s2));   // s1/s2 는 이미 NTT 도메인
  j_c = c; j_b = (uint8_t)b;
```
(3) fire_t1 함수 추가 — `haetae_axisa_fire` 바로 뒤(99행 이후):
```c
#ifdef AXISA_JIG
void haetae_axisa_fire_t1(void){           // T1: 저장 상태로 c·s 재계산(글리치 표적) 후 +y
  polyfixvecl z1; polyvecl cs1; polyveck cs2; poly chat; unsigned int i;
  for (i = 1; i < HAETAE_L; ++i) memset(&cs1.vec[i], 0, sizeof(poly));  // pre-zero (트리거 밖)
  memset(&cs2, 0, sizeof(cs2));
  trigger_high();                          // 창 시작 = full-sign 239행과 동일 위치(c-store+ntt+loop 포함)
  cs1.vec[0] = j_c; chat = j_c; poly_ntt(&chat);
  for (i = 1; i < HAETAE_L; ++i){
    poly_pointwise_montgomery(&cs1.vec[i], &chat, &j_s1.vec[i-1]);
    poly_invntt_tomont(&cs1.vec[i]); }
  polyveck_poly_pointwise_montgomery(&cs2, &j_s2, &chat);
  polyveck_invntt_tomont(&cs2);
  trigger_low();
  polyvecl_cneg(&cs1, j_b & 1); polyveck_cneg(&cs2, j_b & 1);
  polyfixvecl_add(&z1, &j_y1, &cs1);       // 융합 +y (fused 빌드 기준)
  memcpy(g_z1raw, &z1, sizeof(g_z1raw));   // cmd_jig 가 이 버퍼의 SHAKE256 16B 를 회신
}
#endif
```
(4) `simpleserial-haetae.c` `cmd_jig`(140–144행)에 mode 2 분기 + extern:
```c
extern void haetae_axisa_fire_t1(void);    // (haetae_axisa_fire extern 옆)
...
uint8_t cmd_jig(uint8_t *in, uint8_t len){ (void)len;
    if      (in[0] == 0) do_sign();
    else if (in[0] == 2) haetae_axisa_fire_t1();   // ★ T1: c·s 재실행
    else                 haetae_axisa_fire();       // T2: +y 재실행
    uint8_t d[16]; shake256(d, 16, (uint8_t*)g_z1raw, sizeof(int32_t) * HAETAE_L * HAETAE_N);
    simpleserial_put('r', 16, d); return 0x00; }
```

> 물리 렌즈 유의: 클린 `z=y` 는 c·s 외곽루프 **진입 직후**(내부 `poly_ntt` 뒤, 첫 반복 전) 를 abort 하고
> `cs1.vec[0]=c` 저장과 `poly_ntt` 를 **건드리지 않는** 좁은 오프셋 밴드에서만 나온다. 나머지 오프셋은
> 부분/쓰레기(`other`). `run_t1_*` 의 `E_MIN/E_MAX` 로 그 밴드를 좁혀 재스윕할 것.

---

## 빌드 (WSL; arm-none-eabi-gcc 는 Git-Bash PATH 에 없음)

```bash
cd /mnt/c/Users/NSRSGW/ChipWhisperer/chipwhisperer/firmware/mcu/simpleserial-haetae

# 축 A (저항 특성화; EDIT 불필요) — 기존 FSIM 빌드
make clean PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline FAULT_SIM=1
make       PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline FAULT_SIM=1
cp simpleserial-haetae-CW308_STM32F4.hex haetae-baseline-FSIM-CW308_STM32F4.hex

# 축 B-1 (full-sign 클린) — EDIT 1 적용 + T1_CS_ZEROINIT 정의
#   (make 에 CFLAGS 추가: 아래처럼 EXTRA_OPTS 또는 makefile 의 CDEFS 에 -DT1_CS_ZEROINIT 삽입)
make clean PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline FAULT_SIM=1 CFLAGS_LAST=-DT1_CS_ZEROINIT
make       PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline FAULT_SIM=1 CFLAGS_LAST=-DT1_CS_ZEROINIT
cp simpleserial-haetae-CW308_STM32F4.hex haetae-baseline-FSIM-T1-CW308_STM32F4.hex

# 축 B-2 (fast-jig 클린) — EDIT 1(+ T1_CS_ZEROINIT)·EDIT 2 적용. AXISA_JIG 는 FAULT_SIM 자동 포함
make clean PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline AXISA_JIG=1 CFLAGS_LAST=-DT1_CS_ZEROINIT
make       PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline AXISA_JIG=1 CFLAGS_LAST=-DT1_CS_ZEROINIT
cp simpleserial-haetae-CW308_STM32F4.hex haetae-JIG-T1-fused-CW308_STM32F4.hex

arm-none-eabi-size simpleserial-haetae-CW308_STM32F4.elf     # RAM < 192KB 확인
```
> `CFLAGS_LAST` 는 예시 변수명이다. 사용 중인 CW makefile 이 추가 `-D` 를 받는 변수를 확인해
> 거기에 `-DT1_CS_ZEROINIT` 를 넣을 것(없으면 makefile 의 공통 `CDEFS`/`CFLAGS` 에 직접 추가).
> EDIT 2 의 fire_t1 는 항상 cs 를 0화하므로 jig 경로 자체는 `T1_CS_ZEROINIT` 없이도 클린하지만,
> full-sign 교차검증 hex(B-1)에는 반드시 `-DT1_CS_ZEROINIT` 가 필요하다.

---

## 검증 파이프라인 요약 (haetae_recover_t1.py)
- `recover_s1_from_two_traces(z_clean, z_fault, c)` : `diff=_s32((z_clean−z_fault)&0xFFFFFFFF)` →
  `ln_exact`(모든 계수 LN 배수?) 하드 게이트 → 기존 T2 역변환 `recover_s1_from_z1(diff, c)`.
- `verify_s1(rec_s1ntt, true_s1ntt, c)` : (1) **NTT 도메인 768/768 정확 일치**(권위, (-1)^b 부호 흡수),
  (2) `ĉ[k]=0` 복원불가 슬롯 계상, (3) **역NTT 로 계수 도메인 실제 s값** 대조. `full`=완전복원.
- 합성 자기검증 통과: intt 역변환 정확, 완전복원 768/768 + 계수 768, 부호 흡수, 1계수 오류 검출.
