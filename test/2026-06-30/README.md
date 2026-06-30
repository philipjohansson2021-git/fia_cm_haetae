# 2026-06-30 — STM32F4 전체 서명 결함주입: 4변형 비교 (하드웨어/SW 라인주입)

ChipWhisperer-Husky + **CW308 STM32F4(STM32F405, 192KB SRAM)** 에서 **HAETAE-120 전체 서명**을
구동하고, 4변형(`baseline`/`double`/`leeha`/`irv`)을 SW 라인별 결함주입으로 비교.

- 클럭: **HSE 직결 7.37MHz**(PLL 미경유 → 클럭글리치 가능, 통신 정상). 내부168MHz HAL 경로는 flash-WS 버그로 미사용.
- 결정론 DRBG(고정 키·nonce) → 변형 1:1 대조. GOLDEN(무결함 서명 SHAKE16) = `ba9f152c607b207fc6512635ba11388c`.
- 결함지점(슈도라인): UNPACK(1)·SEED(2)·SIGNBIT(3)·LSB(5)·**CS=T1(7)**·**ADDY=T2(8)**·**REJECT=RB(9)**.
  - 이 중 **SEED/SIGNBIT/UNPACK/LSB = Lee-Ha 논문의 4 공격지점**, **CS/ADDY/REJECT = 본 연구(IRV) 지점**.
- 재현 방법·코드: [`code/`](code/) (펌웨어 4파일 + `haetae_recover.py` + 노트북 + 빌드 가이드).

---

## 표 A — 커버리지 (1차 결함, 방출 다이제스트 분류)  → `coverage.csv`

| fault | (Lee-Ha?) | baseline | double | leeha | irv |
|---|:--:|:--:|:--:|:--:|:--:|
| SEED | ✓ | LEAK | blocked | blocked | blocked |
| SIGNBIT | ✓ | LEAK | blocked | blocked | blocked |
| UNPACK | ✓ | LEAK | blocked | blocked | blocked |
| LSB | ✓ | LEAK | blocked | blocked | blocked |
| CS (T1) | — | LEAK | blocked | blocked | blocked |
| ADDY (T2) | — | LEAK | blocked | blocked | blocked |
| **REJECT (RB)** | — | LEAK | blocked | **LEAK** ❗ | blocked |

- **double 7/7, irv 7/7, leeha 6/7**. leeha만 **거부우회(RB)** 누락 — 서명후검증이 검증경계 B2(>서명경계 B1/B0)를 써서 경계초과 z를 통과시킴(B1<B2 사각). IRV의 M2(B0+B1 재검사)가 차단.
- 오탐(FL_NONE) 0: 4변형 모두 정상 서명 불변(GOLDEN).
- baseline ADDY(T2)의 'LEAK'은 EXP1에서 **s1 768계수 100% 단일트레이스 복원**으로 실효성 입증.

## 표 B — 2차 결함 (1차 T2 누설 + 2차 탐지분기 스킵)  → `2ndorder.csv`

| variant | verdict | 메커니즘 |
|---|:--:|---|
| baseline | LEAK | 무방어 |
| double | **LEAK(우회)** | `if(불일치) 무효화` 분기 스킵 |
| leeha | **LEAK(우회)** | `if(검증실패) 무효화` 분기 스킵 |
| **irv** | **blocked** | 무분기 감염 — 스킵할 분기 없음 |

→ detect-and-abort(double·leeha)는 단일 분기 스킵으로 우회되나, **IRV만 생존**. "왜 무분기 감염인가"의 실측 근거.

## 표 C — 비용  → `overhead.csv`, `timing.csv`

| variant | 연산시간(상대) | 코드(text) | 정적RAM(dec) |
|---|:--:|:--:|:--:|
| baseline | 1.000× | 24,556 | 31,168 |
| **double** | **2.000×** | +0.7% | +0.6% |
| leeha | 1.137× | +25.4% | +20.0% |
| **irv** | **1.140×** | +26.3% | +20.7% |

- **irv ≈ leeha (둘 다 ~1.14×, verify-tier), 둘 다 double(2.0×)의 절반 수준.** irv·leeha 코드 +25%는 검증 함수(~6KB) 포함분(Lee-Ha 보고 "+6KB"와 일치).
- ⚠ 비용 정직성: 우리 leeha(+14%)는 apples-to-apples 위해 verify+부분이중(1회)을 포함 — Lee-Ha 보고치(부분이중 +0.39%, 서명후검증 +4.63%)와는 구현 차이가 있음(둘 다 병기). **irv-vs-double(1.14 vs 2.0)** 결론은 이와 무관하게 견고.

## 공격 특성 — 누설 재현율 (baseline, one-shot, 메시지 가변, 3배치)  → `success_rate.csv`

| fault | 재현율 | ~회/누설 | 키복원 | 비고 |
|---|:--:|:--:|:--:|---|
| SEED / UNPACK | 100% | ~1.0 | — | 거부 무관(항상 발현) |
| SIGNBIT / LSB / CS(T1) | ~23% | ~4.3 | — | 거부 의존 (Lee-Ha 보고 ~21%와 일치) |
| **ADDY (T2)** | 83% | ~1.2 | **100%** | **단일 트레이스 직접 s1 복원** |
| REJECT (RB) | 90% | ~1.1 | — | 거부판정 스킵 |

→ Lee-Ha Table 2(LSB·부호비트 21% / 언패킹·시드 100%)를 재현 = 셋업·방법론 교차검증.

---

## 결론 (IRV가 double·leeha 모두 지배)

| | 1차 커버리지 | RB | 2차결함 | 비용 |
|---|:--:|:--:|:--:|:--:|
| double | 7/7 | ✓ | ✗ 우회 | 2.0× |
| leeha | 6/7 | ✗ | ✗ 우회 | 1.14× |
| **irv** | **7/7** | **✓** | **✓ 생존** | **1.14×** |

**IRV는 유일하게** (1) 7지점 전면 차단(RB 포함), (2) 2차 결함 생존(무분기 감염), (3) double의 절반 비용.

## 포지셔닝/정직성
- IRV의 개별 탐지(검증·부분이중·정상성)는 Lee-Ha와 원리 공유 → **차용 인정**. 기여 = **무분기 감염 통합 원리(2차결함 내성) + 서명경계 재검사(RB) + 단일트레이스 T2 공격 + HW 실증**.
- RB는 **본 연구의 위협모델 지점**(Lee-Ha 범위 밖). leeha의 RB 누락은 "verify-after-sign 기법의 구조적 사각(B1<B2)"이지 "Lee-Ha가 틀림"이 아님 — 논문에 정확히 한정.
- 상세: 펌웨어 `code/firmware/`, 설계 `IRV_design_notes`, 포지셔닝 `novelty_positioning`(메인 워크스페이스 1_theory/).

## 한계
- 대리/SW 라인주입(결정론) — 실제 클럭글리치 캠페인(축 A)은 별도(다음). 이 키는 거부반복이 많아 baseline 60.8M cycles(고-거부 샘플) — 상대비는 유효, 절대치는 키 의존.
- RB 'LEAK' = "서명경계 위반 z가 검증 통과"(T2식 키복원 검증은 아님 — 통계적 누설).
