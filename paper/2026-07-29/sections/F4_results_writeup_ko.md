# IRV — STM32F4 전체 서명 오류주입 실험: 상세 결과 정리 (논문 작성용)

> 작성 2026-06-30. 본 문서는 §3 공격 / §4 실험 / §5 대응 / §6 평가 초안을 바로 뽑기 위한
> **상세 결과·해석·정직성·절 매핑** 모음. 원자료: `D:/06_github_desktop/fia_cm_haetae/test/2026-06-30/`.
> 관련: [IRV_design_notes](../../3_firmware/f4_fullsign/IRV_design_notes.md), [novelty_positioning](../../1_theory/novelty_positioning.md).

---

## 1. 실험 개요 (→ §4.1 Setup)

- **타겟**: ChipWhisperer-Husky + CW308 UFO + **STM32F405(Cortex-M4, 192KB SRAM)**.
- **알고리즘**: HAETAE-120(MODE2). R_q=Z_q[x]/(x²⁵⁶+1), q=64513, Lₙ=8192, M=3(s₁), L=4, K=2, 서명경계 B1/B0, 검증경계 B2(**B0,B1 < B2**).
- **클럭**: **HSE 직결 7.37MHz**(CW HS2 외부클럭). PLL 미경유 → 클럭글리치가 코어에 직접 전달 + UART 정상. (내부 168MHz HAL 경로는 flash wait-state 버그로 미사용.)
- **RNG**: 고정 시드 결정론 DRBG → 4변형이 동일 키·동일 nonce → 1:1 대조. 무결함 서명 다이제스트 GOLDEN=`ba9f152c607b207fc6512635ba11388c`.
- **펌웨어**: 단일 서명 함수(`haetae_sign_cm`) + 컴파일타임 `VARIANT` 매크로(baseline/double/leeha/irv). 오류는 하드웨어 글리치(축 A) 또는 `-DFAULT_SIM` SW 라인주입(축 B)으로.
- **두 축**:
  - **축 A (HW 클럭글리치)** — 실재성. 본 회차는 미수행(향후); 표적 연산 트리거(c·s~+y) 준비됨.
  - **축 B (SW 라인주입)** — 대응기법 공정 비교. 슈도코드 라인을 결정론적으로 스킵/변조. 본 문서 결과 전부.

### 1.1 오류 지점(슈도 라인) ↔ Lee-Ha 매핑
```
Sign(M, sk):
 1: s1,s2,A ← unpack_sk(sk)            FL_UNPACK  ── Lee-Ha 3.2.2 (언패킹)
 2: seed ← H(key, rnd, μ)              FL_SEED    ── Lee-Ha 3.2.4 (샘플링 시드)
 repeat:
   3: (y1,y2,b) ← SampleHyperball(seed) FL_SIGNBIT ── Lee-Ha 3.2.3 (부호비트 b)
   5: lsb ← LSB(round(y0))             FL_LSB     ── Lee-Ha 3.2.1 (LSB)
   7: cs ← c·s          FL_CS  = T1  ── 본 연구 (c·s 스킵 → z≈y, nonce)
   8: z  ← y + (-1)^b cs FL_ADDY= T2  ── 본 연구 (+y 스킵 → z=c·s, s1 직접) ★
   9: if ‖z‖≥B1(or B0): continue  FL_REJECT = RB ── 본 연구 (거부판정 스킵)
```
- **Lee-Ha 4지점**: SEED·SIGNBIT·UNPACK·LSB. **본 연구 3지점**: CS(T1)·ADDY(T2)·REJECT(RB).

---

## 2. 공격 분석 (→ §3)

### 2.1 표적 연산과 오류 효과
서명 응답 `z = y + (−1)ᵇ c·s₁` 에서:
- **T1 (c·s 스킵)**: z≈y → 마스킹 nonce 노출(다수 서명+격자로 키복원; Espitau류).
- **T2 (+y 스킵)**: z = (−1)ᵇ Lₙ·(c·s₁). c 공개 → **단일 트레이스 직접 s₁ 복원**. 본 논문 주표적.
- **RB (거부판정 스킵)**: 서명경계(B1/B0) 초과 z 방출 → 통계적 키정보. **검증경계 B2가 느슨해(B1<B2) 표준 검증을 통과**할 수 있어 위험.
- Lee-Ha 4지점: LSB·언패킹(→도전값 c 오염, 차분 키복원), 부호비트(→차분 2c·s₁), 시드(→예측가능 y).

### 2.2 T2 단일 트레이스 키복원 (수학·실측)
누설식: z/Lₙ = (−1)ᵇ c·s₁ (mod q). NTT로 합성곱→성분곱:
> **ŝ₁[k] = NTT(z/Lₙ)[k] · ĉ[k]⁻¹ (mod q)**, ĉ=NTT(c), ĉ[k] 가역(q 소수, 본 파라미터 확인).
- 부호 (−1)ᵇ 및 "깨끗한 T2" 판정: 응답 vec0가 ±Lₙ·c 와 일치하는지로 공격자가 자가확인.
- **실측(EXP1)**: STM32F4 전체 서명에서 T2 오류 응답 z₁ → s₁ 768계수(3×256) **전부 100% 복원**(레퍼런스 산술과 일치, clean_T2=True). → IRV 초안 §7.2가 "향후과제"로 남긴 *전체서명 단일트레이스 복원*을 실기기에서 닫음.

### 2.3 지점별 공격 난이도 — 누설 재현율 (EXP3, one-shot·메시지 가변·3배치)
| 지점 | 재현율 | ~회/누설 | 키복원 | 해석 |
|---|:--:|:--:|:--:|---|
| SEED, UNPACK | **100%** | ~1.0 | — | 거부 무관(결정론 오염→항상 발현) |
| SIGNBIT, LSB, CS(T1) | **~23%** | ~4.3 | — | 거부 의존(오류 z가 거부샘플링 통과해야) |
| **ADDY (T2)** | **83%** | ~1.2 | **100%** | 단일 트레이스 직접복원; 발현 시 전부 키복원 |
| REJECT (RB) | **90%** | ~1.1 | — | 거부판정 스킵 |
- **Lee-Ha 교차검증**: 우리 SIGNBIT/LSB ~23% ≈ Lee-Ha Table 2의 **~21%**(리젝션 1회 통과확률), UNPACK/SEED **100%** 일치 → 셋업·방법론 신뢰성 확인.
- 배치별 분산: ~23% 그룹은 N=10 표본노이즈로 큼(SIGNBIT [10,10,50] 등) → 논문 신뢰구간은 M=30~50 재측정 권장. 평균은 유효.

---

## 3. 대응기법 (→ §5)

| 변형 | 내용 | 출력 무효화 방식 |
|---|---|---|
| baseline | 무방어 레퍼런스 서명 | — |
| double | 전체 이중연산(2회 서명 비교) | `if 불일치 → 0xFF` (분기) |
| leeha | Lee-Ha 재구현: 서명후검증 + 정상성 + 시드재유도 + 부분이중연산(채택 1회) | `if 검증실패 → 0xFF` (분기) |
| **irv** | IRV (아래) | **무분기 감염**(δ≠0→난수화) |

### 3.1 IRV 메커니즘 (무분기 감염형 통합)
모든 잔차를 단일 누산기 δ에 OR로 모으고, 마지막에 무분기 마스킹. δ=0이면 서명 불변(오탐 0).
- **M3** 키 체크섬(서명 전): 영속 키 변조.
- **M1** c·s 재계산(δ에 XOR): T1·T2·loop-abort·데이터변조 — **무분기**.
- **M2** 노름 재검사 **B1+B0**: **거부우회 RB** — **무분기**. ★ verify-after-sign의 사각을 메움.
- **M1b** 시드 정상성: SEED — 무분기.
- **M1c** 부호/논스 재유도(채택 1회): SIGNBIT — 무분기.
- **M1′** 표준검증(서명 밖 main): LSB·UNPACK("자기일관적이나 무효한 서명"). (스택 절약 위해 서명 함수 밖.)
- **M4** 무분기 감염: factor=(δ≠0)?0xFF:0; sig ^= PRF(비밀시드‖δ)&factor.

### 3.2 핵심 통찰 — 순진한 서명후검증의 불충분성 (B1 < B2)
HAETAE 검증경계 B2는 서명경계 B1/B0보다 **느슨**. 거부판정 스킵으로 생성된 경계초과 z는 **B1은 위반하나 B2는 만족**할 수 있어 **표준 Verify를 통과** → verify-after-sign(leeha)이 RB를 놓침. IRV의 M2는 **서명경계로** 재검사하여 차단.

### 3.3 무분기 감염 원리 (신규성 핵심)
기존 대응(double·verify-after-sign)은 전부 **탐지-후-중단**(`if 오류 → 중단/무효화`) = 데이터 의존 **단일 분기**. 2차 오류로 그 분기 하나를 스킵하면 우회됨. IRV는 잔차를 **무조건** 출력에 확산 → 뒤집을 boolean 분기가 없음(2차 오류 내성). 저자 2013 RSA-Fermat 감염형의 격자 FS 확장.

---

## 4. 평가 결과 (→ §6)

### 표 A — 커버리지 (1차 오류, 방출 다이제스트 분류)  [coverage.csv]
| fault | baseline | double | leeha | irv |
|---|:--:|:--:|:--:|:--:|
| SEED / SIGNBIT / UNPACK / LSB | LEAK | blocked | blocked | blocked |
| CS (T1) / ADDY (T2) | LEAK | blocked | blocked | blocked |
| **REJECT (RB)** | LEAK | blocked | **LEAK** | blocked |
| **합계 차단** | 0/7 | **7/7** | **6/7** | **7/7** |
| 오탐(FL_NONE) | — | 0 | 0 | 0 |

- baseline 전 지점 유출(ADDY는 100% 키복원 실증). **leeha만 RB 누락**(B1<B2). irv·double 7/7. 오탐 0.

### 표 B — 2차 오류 (1차 T2 누설 + 2차 탐지분기 스킵)  [2ndorder.csv]
| variant | 결과 | 메커니즘 |
|---|:--:|---|
| baseline | LEAK | 무방어 |
| double | **LEAK(우회)** | 비교 분기 스킵 |
| leeha | **LEAK(우회)** | 검증 분기 스킵 |
| **irv** | **blocked** | 무분기 감염(스킵할 분기 없음) |
- 방출 다이제스트: baseline·double·leeha 모두 `63ff5e…`(=T2 누설), irv `3cbd14…`(=감염 마스킹). **IRV만 생존.**

### 표 C — 비용  [overhead.csv, timing.csv]
| variant | 연산시간(상대) | text(코드) | dec(정적RAM) |
|---|:--:|:--:|:--:|
| baseline | 1.000× | 24,556 B | 31,168 B |
| double | **2.000×** | +0.7% | +0.6% |
| leeha | 1.137× | +25.4% | +20.0% |
| **irv** | **1.140×** | +26.3% | +20.7% |
- irv ≈ leeha(둘 다 ~1.14×, 검증 포함 +25% 코드), **둘 다 double(2×)의 절반**. (baseline 60.86M cycles — 본 키는 거부반복 多.)

### 4.1 종합 (지배 관계)
| | 1차 커버리지 | RB | 2차오류 | 비용 |
|---|:--:|:--:|:--:|:--:|
| double | 7/7 | ✓ | ✗ 우회 | 2.0× |
| leeha | 6/7 | ✗ | ✗ 우회 | 1.14× |
| **irv** | **7/7** | **✓** | **✓ 생존** | **1.14×** |
> **IRV는 유일하게** (1) 7지점 전면 차단(RB 포함), (2) 2차 오류 생존, (3) double 절반 비용.
> double 대비: 동일 커버리지지만 2차오류 취약 + 2× 비용. leeha 대비: RB 추가 커버 + 2차오류 내성, 동일 비용.

---

## 5. 정직성 / 한계 (논문에 반드시 명시)

1. **차용 인정**: IRV의 M1′(검증)·M1c(부분이중)·M1b(정상성)은 Lee-Ha의 탐지와 원리 공유. 기여는 *새 탐지*가 아니라 **무분기 감염 통합(2차오류 내성) + 서명경계 재검사(RB) + 단일트레이스 T2 공격 + HW 실증**.
2. **RB framing**: RB는 **본 연구 위협모델 지점**(Lee-Ha 범위 밖). leeha의 RB 누락은 "verify-after-sign 기법의 구조적 사각(B1<B2)"이지 "Lee-Ha가 틀림"이 **아님**. 정확히 한정.
3. **leeha 비용 재구현 차이**: 우리 leeha +14%(verify+부분이중 1회, irv와 apples-to-apples) vs Lee-Ha 보고 ~+5% → **둘 다 병기**. irv-vs-double(1.14 vs 2.0)은 무관하게 견고.
4. **RB 'LEAK' 범위**: "서명경계 위반 z가 검증 통과"를 뜻함(T2식 키복원 100% 검증은 아님 — RB는 통계적 누설). 주장 한정.
5. **2차오류 위협모델**: "출력-게이팅 *조건분기* 1회 스킵". irv 생존은 응답연산 핵심(T1/T2/RB)의 무분기 감염 덕분. (LSB/UNPACK는 irv도 main 검증분기로 잡아 그 지점 2차오류엔 취약 — 응답연산 한정 주장.)
6. **대리/SW 주입**: 본 회차는 결정론 SW 라인주입(축 B). 실 클럭글리치(축 A) 실재성·확률성은 향후. 결정론 DRBG는 1:1 대조용(배포 아님).
7. **키 의존 절대치**: baseline 60.86M cycles는 본 키의 높은 거부반복 탓 — **상대비**는 유효, 절대치는 키 의존.

---

## 6. 주장 ↔ 데이터 ↔ 논문 절 매핑

| 주장 | 데이터 | 논문 절 |
|---|---|---|
| T2 단일트레이스 s1 100% 복원(전체서명·HW) | EXP1, EXP3(ADDY 키복원83%) | §3.3, §4.4 |
| 지점별 공격 재현율(난이도), Lee-Ha 재현 | EXP3 / success_rate.csv | §3, §4 |
| 커버리지: irv 7/7, leeha RB 누락 | EXP2 / coverage.csv | §6.2 (표 A) |
| 2차오류: irv만 생존 | EXP4 / 2ndorder.csv | §6.x (표 B) ★ 신규성 |
| 비용: irv≈leeha, double 2× | EXP5/6 / overhead·timing.csv | §6.4 (표 C) |
| verify-after-sign의 RB 사각(B1<B2) | EXP2 REJECT(leeha LEAK vs irv blocked) | §5.3 |
| 무분기 감염 원리(2013 계보) | EXP4 + 설계 | §5.1, §8.3 |

## 7. 재현
- 펌웨어 4파일 + `haetae_recover.py` + 노트북 + 빌드가이드: `test/2026-06-30/code/`(+`README_build.md`).
- 빌드: `make PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=<v> [FAULT_SIM=1]`.
- F4 HAL: `git submodule update --init firmware/mcu/hal/chipwhisperer-fw-extra`.
- 노트북: SETUP→BUILD→SMOKE→EXP1~6.

## 8. 축 A 물리 실현성 (2026-07-05 완료) + 향후
- **축 A(HW 클럭글리치) 완료**: real full-HAETAE +y 스윕(N≈650) → **clean T2 0건**(crash/다른 유효 서명만), 복구 self-test **100%**. **레퍼런스 융합 +y(`z₁[i]=y₁[i]+Lₙ(c·s₁)[i]` 1-shot)가 단일 글리치 clean T2를 물리적으로 차단** → SW 오류모델 = 방어자 상한. 정리: `D:/06_github_desktop/fia_cm_haetae/test/2026-07-05/`(README·fig_sw_vs_phys_T2·fig_axisA_outcome·fig_fault_characterization·CSV).
- 향후 물리 실현: 2단계 응답 구현 변형 / T1 차분(2-trace) / 다중오류·EM 주입 / 절대 성공률·파라미터 맵.
- 표 A/B/C 그림화(막대·히트맵).
- §3 그룹 재현율 M=30~50 재측정(신뢰구간).
- (선택) leeha 부분이중 추가 경량화 / Lee-Ha 코드 확인.
