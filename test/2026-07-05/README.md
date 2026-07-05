# 2026-07-05 — 축 A(하드웨어 클럭글리치) T2 물리 실현성 연구 (real full-HAETAE)

STM32F4(CW308+Husky, HSE 직결 7.37MHz)에서 **실제 클럭글리치**로 HAETAE 전체 서명의
**T2(+y 스킵)** 를 물리적으로 유발하려 시도하고, 자율 파라미터 탐색으로 결함을 특성화한 날.

> **핵심 발견**: **레퍼런스의 융합 +y(`z1 = y1 + LN·c·s1`)에서는 단일 클럭글리치가 clean T2 누설을
> 물리적으로 만들지 못한다.** SW 결함모델(축 B, +y 통째 스킵 → s1 100%)은 **방어자 관점의 상한(upper bound)**이며,
> 물리 단일-트레이스 공격은 융합 모듈러 산술의 암묵적 내성에 막힌다. (fault-model ↔ 물리 간극 = 본 절 기여)

7/2~7/5의 미아카이브 작업(07-01 축 A 셋업 이후)을 오늘 날짜로 정리.

---

## 무엇을 했나

1. **독립 실험환경 aifia**(conda, Python 3.11) 구성: `chipwhisperer 6.0.0` editable(레포와 동일) + numpy/pandas/scipy/jupyterlab. 실행 배치 `run_aifia.bat`(폴더 루트로 Jupyter Lab, 펌웨어 빌드는 WSL 연결).
2. **축 A 노트북(`Lab_HAETAE_F4_EXP7_AxisA`) 리뷰·수정** (ChipWhisperer 예제 대비):
   - `glitch_once`의 **읽기 timeout 버그 수정** — `simpleserial_read_witherrors`의 정상프레임 `timeout`이 기본 250ms라 **8초 서명이 매번 mute**로 오판되던 문제(이전 "글리치 미주입"처럼 보이던 원인) 해결.
   - 트리거=공격지점(`T` 커맨드, ADDY=+y), arm 전 크래시 선체크, 부분누설 복구(`PartialAccumulator`) 추가.
3. **펌웨어는 실제 full-HAETAE +y 유지**(인위적 계측/가드 없음 — F3식 간이화 배제). FSIM hex 4종 재빌드(WSL).
4. **자율 드라이버 닫힌-루프**(독립 python, `t2_driver.py`/`t2_char.py`): p1 광역 스캔 + 결함 특성화. 결과를 CSV/JSON/그림으로 저장.
5. **복구 self-test**: SW로 +y 스킵(z1=LN·c·s1) → 직접복구 **s1 100%** — 복구식·스트리밍·펌웨어 정상 확인(0% 결과가 "복구 고장"이 아님을 배제).

---

## 표 A — 축 A 단일 클럭글리치 결과 (real HAETAE +y, N=300) → `figures/fig_axisA_outcome`

| 결과 | 수 | 비율 | 의미 |
|---|--:|--:|---|
| golden | 274 | 91.3% | 무영향 (또는 거부샘플링이 결함을 마스킹 → 깨끗한 재시도) |
| mute (crash) | 21 | 7.0% | 타깃 크래시 — **글리치가 칩에 도달**했다는 직접 증거 |
| other (garble) | 5 | 1.7% | 채택된 **오염 서명** |
| **LEAK (clean T2)** | **0** | **0.0%** | **clean 단일-트레이스 T2 누설 없음** |
| clean_coef (부분누설 계수) | **0** | — | accepted-fault도 **y-스킵된 계수 0** (부분누설도 없음) |

- 광역 스캔: `ext ∈ [0, 15568](+y 창 전체) sweep · width 30–75 · offset ±15 · repeat {1,1,2}`, 8.3s/샷.
- 글리치는 확실히 주입됨(mute 21). 그러나 **부분누설 복구가 한 계수도 수확 못 함**(coverage 0/768).

## 표 B — SW 모델 vs 물리 현실 (T2 단일트레이스 s1 복원) → `figures/fig_sw_vs_phys_T2`

| 방식 | s1 복원율 | 트레이스 | 근거 |
|---|--:|--:|---|
| **SW 결함모델**(축 B, +y 통째 스킵) | **100%** | 1 | 2026-06-30 EXP1 (`clean_T2=True`) |
| **물리 클럭글리치**(단일 결함) | **0%** | — | 본 절 p1 (N=300, best_s1=0%) |

## 왜 — 레퍼런스의 융합 +y 구조

```c
// polyfix.c: 응답 계산은 y와 c·s1을 한 번에 z1에 기록(융합)
z1[i] = y1[i] + LN · (c·s1)[i];     // cs1이 z1에 '단독'으로 저장되는 순간이 없음
```

- 이 융합 덧셈을 글리치하면 z1[i]는 **garble**(쓰레기값)이 될 뿐 `LN·(c·s1)[i]`(=clean 누설)가 되지 않음.
- clean 누설이 되려면 **y1[i] 로드가 정확히 0**으로 읽혀야 하는데(그래야 z1[i]=LN·cs1[i]), 관측되지 않음.
- 반면 **SW 모델·F3**는 z1을 `LN·c·s1`로 **명시적으로 계산**하므로 100%가 나옴 → **SW는 상한**.

## 결함 특성화 (진행 중 — 완료 시 갱신) → `figures/fig_fault_characterization`

기준값 2개(결정론 키): `z1_normal`(정상), `z1_cleanleak`(SW +y 스킵 = 이상적 `LN·c·s1`).
accepted-fault마다 `n_changed`(정상과 다른 계수) / `n_cleanleak`(이상적 누설값과 일치=진짜 y-스킵) / `n_garble` 측정.
→ **n_cleanleak > 0인 fault가 하나라도 있으면 부분 T2 물리 가능**, 전부 0이면 융합내성 확정. (표/그림은 char 배치 완료 후 채움)

---

## 결론 / 논문 함의

- **단일-트레이스 T2 직접복구는 SW 모델에선 자명(100%)하나, 레퍼런스 융합 +y에선 물리적으로 재현되지 않는다.**
  → 융합 모듈러 산술의 **암묵적 내성** + **fault-model ↔ 물리 실현성 간극**을 기여로 제시.
- 공격·복구·대응기법 **정량 실증은 SW(축 B)+x86 coverage로 완결**(2026-06-28/06-30): T2 s1 100%, IRV coverage 7/7·2차결함 생존·비용 1.14×.
- 따라서 **물리 T2 성공 없이도 논문 성립**: SW 공격/대응(코어) + 축 A 물리 실현성 연구(융합내성 발견)로 구성. 물리 성공은 보너스.

## 다음

- 결함 특성화(char) 완료 → `n_cleanleak` 분포로 융합내성 최종 확정 + 그림 추가.
- (향후과제) 물리 누설을 원하면: 2단계 구현 변형(`z1=cs1` 후 `+y`) 대상 / T1(c·s1 스킵)–정상 차분(2-trace) / EM·다중결함.

## 파일

```
code/
├─ Lab_HAETAE_F4_EXP7_AxisA.ipynb   축 A 노트북(트리거=공격지점, 부분누설 복구, timeout 수정)
├─ haetae_recover.py                T2 직접복구 + PartialAccumulator(부분누설 누적)
├─ t2_driver.py                     자율 파라미터 탐색 드라이버(독립 실행, 실시간 로그)
├─ t2_char.py                       결함 특성화(z1_normal/cleanleak 대비 n_changed/n_cleanleak)
├─ run_aifia.bat                    aifia + ChipWhisperer Jupyter 실행 배치
└─ firmware/                        real full-HAETAE (haetae_sign_cm.c 융합 +y · simpleserial-haetae.c · fault_sim.h · makefile)
results/
├─ t2_log.csv, t2_summary.json      p1 광역 스캔(300샷) 로그·요약
├─ t2_char.csv                      결함 특성화 로그
└─ exp7_glitch_log.csv, exp7_variants.csv   노트북 EXP7-b/d 산출
figures/
├─ fig_axisA_outcome.{png,pdf}      표 A 그림
├─ fig_sw_vs_phys_T2.{png,pdf}      표 B 그림 (SW 100% vs 물리 0%)
└─ fig_fault_characterization.{png,pdf}   결함 특성화(char 완료 후)
```

> 재현: `run_aifia.bat` → 노트북 위→아래, 또는 `t2_driver.py`(config JSON으로 범위 지정). 서명 1회 ~8초.
> 정직성: 결정론 키(복구 오라클은 랩 편의), SW 모델 = 방어자 관점 상한.
