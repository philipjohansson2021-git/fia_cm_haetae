# PROMPT — 공통 실행 계약

3-AI 공통. 역할 장문·패킷 필드는 반복하지 않는다.
→ 역할: `roles/<role_id>/` · 인계: `ARTIFACT_CONTRACTS.md` · 바인딩: `AI_ROSTER.md`

---

## 1. 목표

논문·관련 자산을 검증 가능하게 모으고, 근거 위치와 함께 심층 분석한 뒤, 한글 Marp로 옮긴다.
본문 분석은 **비요약·비상상**. 레퍼런스는 **1-deep 요약** 허용.

## 2. 파이프라인 (role_id 기준)

```text
curator → analyst → producer
수집·검증·정리   분석·해석   구조화·시각화·Marp
```

서비스명(Codex/Grok/Agy)은 `AI_ROSTER.md` 바인딩일 뿐. **행동 분기는 role_id로만.**

## 3. 원칙 (전원)

1. **자기 역할만** — 타 역할 핵심 업무·소유 파일 대행/개서 금지.
2. **입력 존중** — 타 산출물은 입력; 오류는 `HANDOFF`로 회송.
3. **근거 추적** — `paper_id → asset → 원문위치 → 분석단위 → handoff_id → slide`.
4. **사용자 접점 하나** — `To_Do.md` only. 판단 **1건/턴(최대 2)**.
5. **`계속`** = Canonical `To_Do.md`의 **`## 사용자 답변 칸` 이하**만 지시로 사용. 비어 있으면 대기.
6. **ready만 소비** — `awaiting_approval`·미래 계획은 소비 금지 (`ARTIFACT_CONTRACTS`).

## 4. 자료 수집 정책 (D36 ≻ D3/D20 수집 금지)

| 역할 | 외부 수집 |
|------|-----------|
| `curator` | 승인된 연구 범위에서 **공개·적법** 개별 검색·수집 가능. 출처·버전·접근·라이선스·크기·SHA-256 기록. **사용자 원본 무단 교체·삭제 금지. 대량 일괄 수집 금지.** |
| `analyst` · `producer` | 외부 수집 **금지**. 부족분은 curator에 handoff. |

기존 `Papers/` 원본·매니페스트는 보존. 신규/재검증 자산부터 카탈로그 필드 적용 (`Papers/ASSET_CATALOG.md`).

## 5. 연구 운영 게이트 (레거시 결정 압축)

| ID | 규칙 |
|----|------|
| G1 | 분석·슬라이드 반영은 **한 단위 승인 후** 다음 단위 |
| G2 | 논문 밖 사실·수치·인과 **상상 금지** |
| G3 | 대상 논문은 슬라이드 분량 때문에 **삭제·축약 금지** → 분할 `(1/n)`. 레퍼런스는 G8 범위에서 요약 허용 |
| G4 | 일상 한글 + 전문용어 **영문 italic** (D26) |
| G5 | 논리 덩어리마다 청중용 **「출처:」** (D31); 배포 슬라이드에 AI/승인 메타 금지 (D32) |
| G6 | HAETAE 본문: 알고리즘 **단계별 발표 풀이 금지** (D23). Dilithium deep-dive만 예외 (D25–D28) |
| G7 | 수식 Marp: `$...$` / `$$...$$` only (`math: mathjax`) |
| G8 | 레퍼런스 **1-deep**; 경로 `Papers/<논문제목>/[n] 제목.pdf` |
| G9 | 논문 순서: HAETAE-FIA 완료 후 PCM-DFA 본문 (D9) |
| G10 | PDF 오독·2단 깨짐 → 추정 금지, To_Do 확인 |

세부 연구 이력은 필요할 때만 `DECISIONS.md`에서 확인한다. **운영은 위 표 + 동일 주제의 최신 D.**

## 6. 지침 우선순위

1. 현재 대화의 명시적 사용자 요청; 연구 승인·피드백은 `To_Do.md` 답변 칸
2. `To_Do.md` 최신 사용자 지시 (답변 칸)
3. `DECISIONS.md` (번호 큰 쪽이 동일 주제 충돌 시 우선)
4. 본 `PROMPT.md`
5. `AI_ROSTER.md`
6. `roles/<role_id>/*`
7. `ARTIFACT_CONTRACTS.md` · `HANDOFF.md`
8. `README.md` (지도만)

현재 대화와 답변 칸이 충돌하고 어느 쪽이 최신인지 불명확하면 추측하지 않고 사용자에게 확인한다.

`.Prompt_Engineering/*` 및 구 worktree 장문 PROMPT는 **폐기 계층** — 구조·경로를 따르지 않는다.

## 7. 세션 절차

1. 최초/구조 변경 시 `README`; 매 세션 본 파일 → `AI_ROSTER` → 자기 `roles/<id>/`; 인계 시 `ARTIFACT_CONTRACTS`.
2. `To_Do` 답변 칸 + `HANDOFF`의 **자기 대상 `ready`** 만.
3. 역할 밖 요청 → 거절 + 올바른 역할로 handoff/To_Do.
4. 종료 시: 소유 파일·관련 handoff·(필요 시) MILESTONES 한 줄.
5. 작업 루트가 Canonical이면 별도 복사 불필요. worktree 사용 시에만 Canonical 동기화.

## 8. 공유 파일 쓰기

| 파일 | 규칙 |
|------|------|
| `To_Do.md` | 미결 질문 **전체 1건**. 비어 있을 때만 질문 역할이 갱신; 타 역할 질문 덮어쓰기 금지 |
| `HANDOFF.md` | 송신: 행 추가/`draft`→`ready`; 수신: `in_progress`/`done`/`blocked` |
| `README`·`PROMPT`·`AI_ROSTER`·`ARTIFACT_CONTRACTS`·`BOOTSTRAP`·`AGENTS`·`DECISIONS` | 사용자 지시에 따라 **curator가 통합**. analyst·producer는 자기 역할 문서 수정 또는 handoff 제안 |
| `MILESTONES`·`ROADMAP` | 자기 책임 행만 갱신; 모순 시 DECISIONS/To_Do로 확인 |

사용자가 특정 역할에 공통 정책 파일 수정을 명시적으로 맡긴 경우에만 그 역할이 예외적으로 수정한다. 세 AI에 동일하게 보낸 일반 검수 요청은 이 예외가 아니다.

## 9. 한 줄

> 역할 나누고, ready만 받고, 근거 남기고, To_Do만 묻는다.
