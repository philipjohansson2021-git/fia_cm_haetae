# PARAGRAPH_INDEX — HAETAE-FIA

상태: **confirmed** (H-M2 — 2026-07-21, 사용자 `계속` → 권장 기본값)  
작성일: 2026-07-21  
비고: PDF 2단 편집으로 문단 경계는 **의미 완결 단위**. H-M3 중 경계 수정 가능.  
페이지: 저널 쪽수(약 429–442) 기준 추정. PDF 파일 쪽수 ≈ 저널쪽 − 428.

상태 값: `pending` | `in_progress` | `approved` | `blocked`

---

## 0. 프론트매터

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-001 | 0 | 429 | 제목·저자·소속 (한/영) | approved | 표지 |
| P-002 | 0 | 429 | 요약 | approved | 2장 |
| P-003 | 0 | 429 | ABSTRACT | approved | 슬라이드 제외(D17) |
| P-004 | 0 | 429 | Keywords | approved | 슬라이드 제외(D18) |
| P-005 | 0 | 429 | 연구비·접수일·저자 연락처 각주 (부록 단위) | approved | 슬라이드 제외(D19) |

## 1. I. 서론

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-006 | I | 429–430 | 양자 위협·NIST PQC·ML-DSA·KpqC·HAETAE 최종후보 | approved | 슬라이드 |
| P-007 | I | 430 | HAETAE 설계 특징(Module-LWE, Bimodal, 부채널 내성) | approved | 슬라이드 |
| P-008 | I | 430 | 구현 환경의 공격 표면·FI 수단·기존 암호 FI 위험 | approved | 슬라이드 |
| P-009 | I | 430 | Dilithium FI 연구 vs HAETAE 연구 공백 | approved | 슬라이드; [9–12] PDF 확보 |
| P-010 | I | 430 | 본 논문 목적·네 공격 지점·실험·대응 기여 요약 | approved | 슬라이드 |

## 2. II. 관련 연구 및 배경 지식

### 2.1 KpqC HAETAE 서명 알고리즘

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-011 | 2.1 | 430 | HAETAE 명칭·목표(서명·검증 키 크기, hyperball rejection, 최대 39%) | approved | 슬라이드 |
| P-012 | 2.1 | 430 | 키 생성: MLWE, Truncation, 비밀키 \(s_1,s_2\), 노름 조건 | approved | 참조만(D23) |
| P-013 | 2.1 | 430–431 | 서명: Fiat–Shamir with aborts, seed·expandYbb, \(y\) 샘플링 | approved | 참조+최소 식 |
| P-014 | 2.1 | 430–431 | Fig. 1 — Bimodal Hyperball Uniform Distribution | in_progress |
| P-015 | 2.1 | 431 | Bimodal 중심 둘·rejection·서명 크기와 \(y\) | pending |
| P-016 | 2.1 | 431 | 도전값 \(c\), 서명 벡터 \(z\) 정의, Fig. 2 지시 | pending |
| P-017 | 2.1 | 431 | Fig. 2 / 알고리즘 — HAETAE signature (steps 1–16 단위) | pending |
| P-018 | 2.1 | 431 | 검증: \(z\) 재구성, hint \(h\), 도전값 비교 | pending |

### 2.2 오류 주입 공격

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-019 | 2.2.1 | 431 | FI 정의·능동적 공격·Bellcore RSA[7] | pending |
| P-020 | 2.2.1 | 431 | AES/ARIA/RSA/ECC 및 Dilithium 등 FI 연구 흐름 | pending |
| P-021 | 2.2.1 | 431 | 물리적 오류 수단과 보안 영향 | pending |
| P-022 | 2.2.2 | 431–432 | 분석 기법 소개 범위 [19–22], 본 논문 사용 기법 | pending |
| P-023 | 2.2.2.1 | 431–432 | Skipping Fault Attack 정의 | pending |
| P-024 | 2.2.2.1 | 432 | 격자 서명·HAETAE에서의 스킵 취약 구조 | pending |
| P-025 | 2.2.2.2 | 432 | DFA 정의·역사·범용성 [9,13–15] | pending |
| P-026 | 2.2.2.2 | 432 | DFA 차분 \(\Delta O = O - O'\) 원리 | pending |

## 3. III. HAETAE 서명 알고리즘 오류 주입 공격

### 3.1 공격 모델

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-027 | 3.1 | 432 | 공격 모델 절 도입 | pending |
| P-028 | 3.1 | 432 | 공격자 가정 및 능력 (물리 접근·스킵/비트플립·정상/오류 서명) | pending |
| P-029 | 3.1 | 432 | 공격 목표 (\(s_1\) 복구·위조 서명·FS with Aborts 함의) | pending |
| P-030 | 3.1 | 432 | 정리 3.1 — \(s_1\) 노출 시 위조 서명 가능성 (진술) | pending |
| P-031 | 3.1 | 432–433 | 증명 — 검증식 (1), 위조 구성 (2)(3), hint 역할 | pending |

### 3.2 공격 시나리오

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-032 | 3.2 | 433 | Deterministic HAETAE 대상 선정 이유 | pending |
| P-033 | 3.2 | 433 | 내부 경로 구분: 난수 생성 vs 도전값 생성 | pending |
| P-034 | 3.2.1 | 433 | LSB 공격 — HighBits/LSB 구조·필요성 | pending |
| P-035 | 3.2.1 | 433 | LSB 공격 — 정상 서명 과정 수식 (4) | pending |
| P-036 | 3.2.1 | 433 | LSB 공격 — 오류 주입·차분 수식 (5)·\(s_1\) 복구 | pending |
| P-037 | 3.2.2 | 433–434 | 언패킹 공격 — seed\(_A\)·unpackA·오류 \(\Delta A\) | pending |
| P-038 | 3.2.2 | 434 | 언패킹 공격 — \(w_\mathrm{fault}\) 전파·(3)–(5) 재사용 | pending |
| P-039 | 3.2.3 | 434 | 부호 비트 공격 — Bimodal·\(b\in\{0,1\}\) 역할 | pending |
| P-040 | 3.2.3 | 434 | 부호 비트 공격 — 수식 (6)(7)(8)·\(s_1\) 복구 | pending |
| P-041 | 3.2.4 | 434–435 | 샘플링 시드 공격 — seed\(_{ybb}\)·expandYbb·스킵·초기 0 | pending |
| P-042 | 3.2.4 | 434–435 | Fig. 3 — Key Recovery Algorithm for Sampling Seed Attacks | pending |
| P-043 | 3.2.4 | 435 | 시드 공격 — \(k\) 탐색·\(c\) 일치 시 키 복구 | pending |

## 4. IV. 실험 설계 및 구현

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-044 | 4.1 | 435 | 실험 목적·SW 논리 삽입 + HW 물리 주입·v3.0 펌웨어 | pending |
| P-045 | 4.1 | 435 | HW: STM32F405·CW308·ChipWhisperer-Husky·클럭 글리치 | pending |
| P-046 | 4.1 | 435 | Fig. 4 — Fault injection environment configuration | pending |
| P-047 | 4.2 | 435–436 | SW 검증 목적·네 시나리오·Fig. 5 | pending |
| P-048 | 4.2 | 435–436 | 키·메시지 고정 설정 (재현성) | pending |
| P-049 | 4.2 | 436 | SW 오류 삽입 지점 (poly_lsb, polymat, signbit, xof256 등) | pending |
| P-050 | 4.2 | 436 | SW 결과 — 4종 공격 키 복구 성공(오류 발생 시 100%) | pending |
| P-051 | 4.3 | 436 | HW 검증 도입 — 목표 연산 구간 독립 실행 | pending |
| P-052 | 4.3 | 436 | 글리치 파라미터 탐색 (width, offset, ext_offset)·트리거 | pending |
| P-053 | 4.3 | 436 | Fig. 6 — Parameter distribution for attack success/failure | pending |
| P-054 | 4.3 | 437 | Table 1 — Detected glitch parameters | pending |
| P-055 | 4.3 | 437 | 공격별 유효 글리치 분포 차이·Fig. 7 (LSB assembly) | pending |
| P-056 | 4.3 | 437 | 성공률 정의(rejection 통과 유효 오류)·~7회/1회·100% 복구 | pending |
| P-057 | 4.3 | 437 | Table 2 — Fault injection analysis results by attack target | pending |

## 5. V. 대응 방안

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-058 | V | 437–438 | 대응 장 도입·탐지+저오버헤드·알고/구현 수준 구분 [23–24] | pending |
| P-059 | V | 438 | 평가 지표: text, dec, CPU cycles | pending |
| P-060 | 5.1 | 438 | 알고리즘 수준 대응 목표 (구조·검증 흐름 수정) | pending |
| P-061 | 5.1.1 | 438 | 서명 후 검증 (Sign-then-Verify) 원리·LSB/언패킹 탐지 | pending |
| P-062 | 5.1.1 | 438 | Table 3 — Overhead of Sign-Then-Verify · 한계(부호/시드) | pending |
| P-063 | 5.1.2 | 438 | 리젝션 루프 내부로 시드 생성 이동 — 원리·효과 | pending |
| P-064 | 5.1.2 | 438 | Table 4 — Overhead of moving inside rejection loop · 한계 | pending |
| P-065 | 5.2 | 439 | 구현 수준 대응 목표 (구조 불변·코드 무결성) | pending |
| P-066 | 5.2.1 | 439 | 부분 이중 연산 — 시드·부호비트 이중 비교 | pending |
| P-067 | 5.2.1 | 439 | Table 5 — Partial double operation overhead · 한계 | pending |
| P-068 | 5.2.2 | 439 | 정상성 검사 — XOF 버퍼 all-same/all-zero 탐지 | pending |
| P-069 | 5.2.2 | 439 | Table 6 — Sanity check overhead · 시드 공격 한정 | pending |

## 6. VI. 결론

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-070 | VI | 439–440 | 기여 요약: 네 지점·SW/HW 실증·5% 미만 대응 | pending |
| P-071 | VI | 440 | 복합 대응 필요·중복연산–SNR/마스킹 이슈·향후 연구 | pending |

## 7. References (본문 단위가 아님 — H-M5에서 REF 요약)

| ID | 범위 | 라벨 | 상태 |
|----|------|------|------|
| P-072 | Ref | References 목록 슬라이드용 묶음 (본문 해석 대상 아님; REF-01…24) | pending |

## 8. 저자 소개 (선택)

| ID | § | p. | 라벨 | 상태 |
|----|---|-----|------|------|
| P-073 | 저자 | 442 | 이상원·김윤성·하재철 약력 | pending |

---

## 집계

| 구간 | 개수 |
|------|------|
| 프론트 P-001–005 | 5 |
| 서론 P-006–010 | 5 |
| II P-011–026 | 16 |
| III P-027–043 | 17 |
| IV P-044–057 | 14 |
| V P-058–069 | 12 |
| VI P-070–071 | 2 |
| Ref/저자 P-072–073 | 2 |
| **합계** | **73** |

## 사용자 확인

사용자 확인은 **`To_Do.md` 한곳**에서만 수행한다 (여기 파일을 사용자에게 직접 열라고 하지 않음).  
승인 후 상태 → `confirmed`, H-M3 P-001 시작.
