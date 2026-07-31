# HAETAE-IRV 논문 — 문서 지도 & 핵심 수치 (작성 시작점)

> 논문은 `5_paper/`에 작성(Overleaf 업로드용). `ref_overleaf_paper/`는 **참고만**.
> 작성 전 이 문서로 어떤 자료가 어디 있는지 파악 → 각 절을 해당 소스에서 뽑는다.

## 문서 구성 — 상세 결과 정리(8개 절): `sections/F4_results_writeup_ko.md`
1. 실험 개요 (→§4 Setup): HW·파라미터·HSE클럭·DRBG·펌웨어·두 축, 결함지점↔Lee-Ha 매핑.
2. 공격 분석 (→§3): T1/T2/RB + Lee-Ha 4지점, **T2 단일트레이스 복원 수학 + 100% 실측**, 재현율 표(+Lee-Ha 교차검증).
3. 대응기법 (→§5): 4변형, **IRV M1~M4 메커니즘**, **B1<B2 통찰**, 무분기 감염 원리.
4. 평가 결과 (→§6): **표 A(커버리지)·B(2차결함)·C(비용)** + 종합 지배관계, 실제 수치 전부.
5. 정직성/한계 7항목: 차용 인정·RB framing·leeha 비용 재구현·RB범위·2차결함 위협모델·대리주입·키의존.
6. 주장 ↔ 데이터 ↔ 논문절 매핑 표.
7. 재현 방법.
8. 향후(축A 글리치·그림·재측정).

## 전체 문서 지도 (논문 쓸 때 참고)
| 문서 | 위치 | 용도 |
|---|---|---|
| 상세 결과 정리 | `5_paper/sections/F4_results_writeup_ko.md` | **§3~§6 초안 소스** |
| 포지셔닝/신규성 | `1_theory/novelty_positioning.md` | 기여 주장·Lee-Ha framing·리뷰어 반박 |
| IRV 설계 상세 | `3_firmware/f4_fullsign/IRV_design_notes.md` | M1~M4 메커니즘·이전버전 diff |
| 결함분석 초안(국문) | `5_paper/sections/03_fault_analysis_ko.tex` | §3 LaTeX 기초 |
| §6 평가 영문 초안 | `5_paper/sections/06_evaluation_en.tex` | §6 LaTeX (figures 참조) |
| 그림 생성 스크립트 | `5_paper/figures/make_figures.py` | 표 A/B/C → PDF/PNG |
| 깃허브 결과 | `D:/06_github_desktop/fia_cm_haetae/test/2026-06-30/` | CSV 5종 + README + 재현 code |
| Lee-Ha 스펙 | 메모리 `leeha-paper-spec` | 비교대상 정확 인용 |
| 연구설계서 / 목차 | `1_theory/00_연구설계서.md`, `1_theory/paper_outline_and_writing_plan.md` | 전체 기획 |

## 핵심 수치 (논문 헤드라인)
- **공격**: T2(+y 스킵) → 단일 서명에서 s₁ **768계수 100% 복원**(STM32F4 전체 서명, **결함 모델 하**; 복구 self-test 검증).
- **물리 실현성(축 A, 2026-07-05)**: 실제 클럭 글리치는 레퍼런스 **융합 +y**에서 clean T2 **불가**(crash/다른 유효 서명; N≈650, clean T2 0). **SW=방어자 상한** → fault-model↔물리 간극(기여).
- **커버리지(표 A)**: irv **7/7**, double 7/7, leeha **6/7**(RB 누락), 오탐 0.
- **2차결함(표 B)**: **irv만 생존**(double·leeha 우회) ← 무분기 감염.
- **비용(표 C)**: irv **1.14×** ≈ leeha 1.14×, **double 2.0×**. 코드 irv/leeha +25%, double +0.7%.
- **재현율(공격난이도)**: T2 83%·키복원100% / SIGNBIT·LSB·CS ≈23% / UNPACK·SEED 100% / RB 90%. (Lee-Ha 21%/100% 재현.)
- **→ IRV가 double·leeha 둘 다 지배**: 7/7 커버 + RB + 2차결함 생존 + double 절반 비용.

## 작성 가능 여부
- **§3~§6 작성 완료·정합**(SW 결함 모델 + 축 A 물리 실현성 발견 통합). 축 A 결과·그림·CSV는 `D:/06_github_desktop/fia_cm_haetae/test/2026-07-05/`에 정리(README + fig_sw_vs_phys_T2·fig_axisA_outcome·fig_fault_characterization).
