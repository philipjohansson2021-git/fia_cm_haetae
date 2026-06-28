# fia_cm_haetae — HAETAE 결함주입공격(FIA) 및 대응기법 연구 저장소

격자 기반 양자내성 전자서명 **HAETAE**(KpqC 후보)에 대한 **결함주입공격(Fault Injection
Attack)** 분석과, 이를 막는 **경량 대응기법 HAETAE-IRV** 의 구현·실험·시뮬레이션을 모은
**연구 재현용 저장소**입니다.

> 이 저장소는 **코드·실험·문서(산출물)** 만 담습니다. 논문 원고(LaTeX)는 별도로 관리됩니다.

## 무엇을 하는 저장소인가

1. **공격(Attack).** HAETAE 서명의 응답 계산 `z = y + (-1)^b·c·s1` 에 단일 결함을 주입하면
   비밀키가 노출됨을 보입니다. 특히 `+y` 덧셈을 건너뛰면(T2) `z = L_N·c·s1` 이 방출되어,
   공개값 `c`만으로 **단일 트레이스에 비밀키 `s1`을 직접 복원**할 수 있습니다.
2. **대응기법(Countermeasure).** **HAETAE-IRV** = c·s 재계산 검증 + 서명경계 노름 재검사 +
   비밀키 무결성 검사 + **무분기 감염형(infective) 마스킹**. 탐지-후-중단 방식과 달리
   검사 분기를 두 번째 결함으로 건너뛰는 우회에 강합니다.
3. **실험·시뮬레이션.** ChipWhisperer + STM32F3/F4 클럭 글리치 실험 펌웨어, 호스트 키복원
   도구, 그리고 대응기법 커버리지·오버헤드 시뮬레이션을 제공합니다.

## 폴더 구조

```
fia_cm_haetae/
├─ docs/                     # 알고리즘 설명서
│   ├─ HAETAE_overview_ko.md            # HAETAE 개요·파라미터·결함 민감점
│   └─ HAETAE_signature_algorithm_ko.md # KeyGen/Sign/Verify 상세
├─ fw_simpleserial-haetae-core/  # ChipWhisperer 펌웨어(core-op 타겟, baseline/irv)
│   └─ recovery/recover_s1.c    #   결함 응답 z1 -> 비밀키 s1 복원 도구
├─ experiment/                # x86 계측 서명/하니스
├─ experiment_package/        # x86 시뮬레이션 + 대응기법 소스 + CW 하니스
├─ haetae_reference/          # HAETAE 공식 레퍼런스 구현(출처·MIT, SOURCE.md 참조)
├─ test/                      # 실험·시뮬레이션을 날짜별로 관리 (test/README.md 인덱스)
│   └─ 2026-06-28/            #   대응기법 커버리지·오버헤드 시뮬레이션
├─ LICENSE                    # MIT (레퍼런스 코드는 원 라이선스 유지)
└─ README.md                  # (이 문서)
```

## 주요 결과 (요약)

- **하드웨어 공격(STM32F3, 클럭 글리치, 각 N=62,720):** 무방어 32회 키유출 vs **HAETAE-IRV 0회**
  (95% 신뢰상한 `p<4.8e-5`). 키복원식은 레퍼런스 산술과 비트 단위 일치(768/768).
- **대응기법 커버리지 시뮬(논리수준, 아키텍처 독립):** HAETAE-IRV **82.4% @ ×1.03**,
  전체 이중연산 90.5% @ ×2.0, Lee 등(JKIISC 2026) 통합 64.9% @ ×1.06. (`test/2026-06-28/`)

## 재현 방법(요약)

- **펌웨어:** `fw_simpleserial-haetae-core/` —
  `make PLATFORM=CW308_STM32F3 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline|irv`.
- **키복원:** `fw_simpleserial-haetae-core/recovery/recover_s1.c` (HAETAE 레퍼런스 ntt/reduce와 컴파일).
- **커버리지 시뮬:** `python3 test/2026-06-28/cm_coverage_sim.py`.

## 관련 연구

본 연구는 Lee, Kim, Ha, "Fault Injection Attacks on Post-Quantum Cryptography Algorithm
HAETAE and Their Countermeasures," JKIISC 36(2), 2026 와 독립적이며, **T2 단일 트레이스
직접 복원**(공격)과 **무분기 감염형 대응**(검사-스킵 이차결함 내성)에서 구별됩니다.

## 라이선스

MIT — [LICENSE](LICENSE). `haetae_reference/`의 공식 HAETAE 코드는 원 MIT 라이선스와
저작권 표기를 유지합니다([haetae_reference/SOURCE.md](haetae_reference/SOURCE.md)).
