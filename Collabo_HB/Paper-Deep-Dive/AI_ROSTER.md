# AI_ROSTER — 바인딩 · 쓰기 소유

`role_id` = 안정 식별자. **서비스명 = 교체 가능한 바인딩.**

## 활성 파이프라인

| 순서 | role_id | 서비스 | 직함 |
|------|---------|--------|------|
| 1 | `curator` | Codex | 학술정보·연구자산 큐레이터 |
| 2 | `analyst` | Grok | 연구문헌 심층분석가 |
| 3 | `producer` | Agy | Marp 프레젠테이션 프로듀서 |

```text
curator → analyst → producer
```

## 단독 쓰기

| role_id | 단독 쓰기 | 비고 |
|---------|-----------|------|
| `curator` | `Papers/**`, `roles/curator/**` | 자산 카탈로그 `Papers/ASSET_CATALOG.md` 포함 |
| `analyst` | `.Intermediate_Artifacts/papers/**`, `roles/analyst/**` | Intermediate **전체** 아님 |
| `producer` | `Presentation_Marp/**`, `roles/producer/**` | |

## 공유 (행·섹션 규칙)

| 경로 | 규칙 |
|------|------|
| `To_Do.md` | 미결 질문 1건; 비어 있을 때 질문 역할이 갱신 |
| `.Intermediate_Artifacts/HANDOFF.md` | 송·수신 상태 전이 (`ARTIFACT_CONTRACTS`) |
| `DECISIONS` · `MILESTONES` · `ROADMAP` · `CROSS_CHECK` | PROMPT §8 |
| `PROMPT` · `AI_ROSTER` · `ARTIFACT_CONTRACTS` · `README` · `BOOTSTRAP_PROMPT` · `AGENTS` · `DECISIONS` | curator 통합; 타 역할은 handoff 제안 |

## 바인딩 변경

1. 사용자 지시 → 본 표 수정  
2. `roles/*/ROLE.md`의 “현재 서비스” 한 줄 동기  
3. `DECISIONS`에 D-기록 · `To_Do` 상태 한 줄  
4. 열린 HANDOFF의 from/to 유효성 확인  

축소/확장: 파이프라인 표에서 역할 제거·추가 + `roles/` 패키지.

## 세션 역할 확정

1. 본 표에서 **현재 서비스명 ↔ active role_id**
2. 사용자가 바인딩 변경을 명시하면 표를 먼저 갱신한 뒤 새 role_id 적용
3. 불명이면 To_Do에 확인 1건 후 대기

사용자 작업 지시는 role_id의 **업무**를 정하지만 임시로 다른 역할을 겸임하게 만들지 않는다.
