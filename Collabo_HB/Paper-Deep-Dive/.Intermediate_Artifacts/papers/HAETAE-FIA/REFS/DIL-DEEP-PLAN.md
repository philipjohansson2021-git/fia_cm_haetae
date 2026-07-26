# Dilithium FI 심층 분석 계획 (D25)

상태: **in_progress** (2026-07-22)  
근거: `To_Do.md` 사용자 답변 칸 (동료 논의 후 Dilithium 코어 선행)  
표준 문서: `Papers/…/NIST.FIPS.204_Module-Lattice-Based Digital Signature Standard (CRYSTALS-DILITHIUM).pdf`  
논문 저장소: `Papers/양자 내성 암호 HAETAE에 대한 오류 주입 공격 및 대응 기법/`

---

## 1. 목표

HAETAE 본문 코어(P-014+)에 들어가기 **전에**, 레퍼런스 **[9]–[12]** 의 오류주입 공격을  
**FIPS 204(ML-DSA) 알고리즘 의사코드에 1:1 대응**시켜 비판적으로 이해한다.

- 논문은 **정답지가 아님** (표준화 과정 변경·구현 가정·휴먼에러 가능)
- 알고리즘 라인은 **FIPS 204 원문과 동일**하게 기술 (임의 해석 금지)
- 논문 주장 ↔ 표준 알고리즘 적용 결과 **동일 여부 비교**

## 2. 발표 연도 순 (이른 것부터)

| 순서 | ID | 발표 | 제목 요약 | Marp 순서 |
|------|-----|------|-----------|-----------|
| **1** | **[11]** | TCHES 2023 **No.2** (2023-03-06) | NTT twiddle-pointer FI | **적용됨** (출판순) |
| 2 | [9] | TCHES 2023 **No.4** (2023-08-31) | MLWE→RLWE DFA Dilithium | 적용됨 |
| 3 | [10] | TCHES 2024 **No.3** (2024-07-18) | Correction FA randomized Dilithium | 적용됨 |
| 4 | [12] | FDTC 2024 | Single-trace FI hedged ML-DSA | 적용됨 |

## 3. 논문당 분석 골격 (사용자 5항목)

| # | 항목 | 산출 |
|---|------|------|
| 1 | FI 대상 알고리즘 **라인** 설명 | FIPS 204 Alg 번호·라인 + 논문 Alg 라인 대응표 |
| 2 | 대응 **C 코드** (있으면) | pqm4 등 — 로컬 부재 시 논문 제시 asm/설명만, 상상 금지 |
| 3 | FI가 어떤 값을 어떻게 바꿈 | 오류 전/후 중간값 |
| 4 | 알고리즘을 따라 전파 | Sign/Verify 루프 내 연쇄 |
| 5 | 정상·오류 출력 → **비밀키 복구** | 식·필요 서명 수·전제 |
| + | **비판적 점검** | 표준과 불일치, 구현 가정, 시뮬레이션 전제, 오류 가능점 |

## 4. [11] 단위 분할 (승인 1건/턴)

| 단위 ID | 내용 | 상태 |
|---------|------|------|
| **DIL-11-U1** | NTT 오류 모델 ↔ FIPS **Alg 41 전문** 슬라이드 + 구현 한계 + 불일치 판정 | **done** |
| **DIL-11-U2** | Attack-1 `Sign_Fault_NTT_C` (deterministic) | **done** |
| **DIL-11-U3** | Attack-2 `Sign_Fault_NTT_Y` (대안 $z$ 구현 가정) | **done** (slides) |
| **DIL-11-U4** | Verification-Bypass | **done** |
| **DIL-11-U5** | [11] 정리 | **done** (slide) |
| **DIL-09-U1** | ExpandMask · nonce++ skip | **done** (slides) |
| **DIL-09-U2** | $\Delta z$ · MLWE→RLWE | pending |

이후 [9]→[10]→[12] 동일 골격.

## 5. D23과의 관계

| 결정 | 적용 |
|------|------|
| **D23** | HAETAE **본문** KeyGen/Sign/Verify 슬라이드에서 알고리즘 단계 **풀이 금지** (참조만) |
| **D25** | **Dilithium 레퍼런스 심층 분석** 구간에서는 사용자 지시에 따라 **FIPS 204 라인 단위 풀이 필수**. D23 예외·별도 트랙 |

## 6. 슬라이드 반영 정책

- 심층 단위 **승인 후** Marp에 divider `Dilithium FI Deep-Dive` 아래 누적
- 기존 [9]–[12] **요약 슬라이드 유지** + 심층 슬라이드 **추가** (삭제 금지)
- 수식: `$...$` / `$$...$$` only

## 7. 로컬 C 코드

- 현재 workspace에 pqm4 Dilithium NTT 소스는 **없음**
- 논문이 인용한 pqm4 + 논문 Fig/asm 인용만 사용
- 사용자가 소스를 넣으면 단위 재개 시 라인 매핑 추가
