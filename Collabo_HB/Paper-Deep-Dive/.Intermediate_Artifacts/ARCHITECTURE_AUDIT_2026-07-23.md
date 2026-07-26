# 아키텍처 검수 — 2026-07-23 (v2→v3.1)

## v3에서 고친 것 (다중 AI 패스 후)

| 문제 | 조치 |
|------|------|
| 역할 정의가 README/PROMPT/ROSTER/ROLE에 4중 복붙 | SSOT: 장문은 BOOTSTRAP+ROLE만; 나머지는 표·포인터 |
| worktree 장문 PROMPT(380줄) vs Canonical 단문 **분열** | Canonical v3를 SSOT로 확정, worktree 동기화 |
| `.Intermediate_Artifacts/` 전체를 Grok 소유로 오해 | `papers/`만 analyst; HANDOFF 등 공유 |
| D3/D20 웹 전면 금지 vs curator 수집 역할 **충돌** | D36/D37: curator 공개·적법 개별 수집 허용, 원본 교체·대량 금지 |
| `ready`에 미래 계획·사용자 게이트 혼입 | 계획=MILESTONES; 승인=`awaiting_approval` |
| `consumed` vs `done` | `done` 단일 |
| ROSTER_STATE·장문 동기화 로그 비대화 | ROSTER_STATE 포인터화 |
| 연구 게이트(D23–D32 등) 압축 과정에서 소실 위험 | PROMPT §5 G1–G10 표로 보존 |
| `.Prompt_Engineering` 구 폴더구조 유혹 | 역사 문서 배너: 운영 계약 우선 |
| 자산 메타 경로 없음 | `Papers/ASSET_CATALOG.md` |
| 정책 파일 수정 주체 모호 | 사용자 지시 세션이 수정 + DECISIONS |
| 세 AI가 같은 검수 요청을 받으면 공통 파일을 동시 수정 가능 | 공통 정책 통합자는 curator; 타 역할은 자기 역할 문서 또는 handoff 제안 |
| direct 사용자 요청이 우선순위에 없음 | 현재 대화의 명시적 요청을 1순위로 추가, 연구 승인 기록은 To_Do 유지 |
| 부트스트랩 뒤 curator 없이 DIL-10 analyst 직행 | DIL-10 필수 자산 재검증 패킷을 첫 연구 작업으로 삽입 |
| ASSET_CATALOG와 SCHEMA 열 불일치·가짜 빈 행 | `venue_or_publisher` 열 추가, placeholder 행 제거 |
| ARTIFACT_CONTRACTS를 작업과 무관하게 매번 읽음 | handoff 생성·소비 시에만 읽도록 독해 계층 통일 |

## 보존

- Papers PDF·매니페스트 미이동  
- READING/REFS/presentation 본문 미개서  
- D1–D36 연구 결정 유지 (수집 정책은 D36≻D3/D20)

## 운영 문서 세트 (최소 독해)

최초: `README` → 매 세션: `PROMPT` → `AI_ROSTER` → `roles/<id>/` → 매 턴: `To_Do` · `HANDOFF`  
`ARTIFACT_CONTRACTS`는 handoff 생성·소비 전에만 읽는다.

## 독해량 점검

파일 바이트 기준(토큰 수는 서비스별 tokenizer에 따라 다름):

| 상황 | 역할별 입력량 |
|---|---|
| 평상시 세션 | 약 11.2–11.5KB |
| handoff 생성·소비 세션 | 약 13.2–13.5KB |
| 최초 부트스트랩(README·공통 시작문 포함) | 약 17.2–17.5KB |

`DECISIONS`, `ROADMAP`, `MILESTONES`, `.Prompt_Engineering` 전체를 매 세션 읽지 않는다. 충돌·상태 확인 등 필요 시에만 연다.
