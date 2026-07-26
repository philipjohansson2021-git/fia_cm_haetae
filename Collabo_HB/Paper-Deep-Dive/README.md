# Paper-Deep-Dive

논문·관련 자산을 **수집·검증**하고, 근거가 추적되는 **심층 분석**을 거쳐 **한글 Marp** 발표자료로 만든다.  
3-AI 파이프라인(서비스 바인딩은 교체 가능).

## 파이프라인

| 순서 | role_id | 현재 서비스 | 직함 | 단독 쓰기 |
|------|---------|-------------|------|-----------|
| 1 | `curator` | Codex | 학술정보·연구자산 큐레이터 | `Papers/**`, `roles/curator/**` |
| 2 | `analyst` | Grok | 연구문헌 심층분석가 | `.Intermediate_Artifacts/papers/**`, `roles/analyst/**` |
| 3 | `producer` | Agy | Marp 프레젠테이션 프로듀서 | `Presentation_Marp/**`, `roles/producer/**` |

```text
curator: 수집·검증·정리  →  analyst: 분석·해석  →  producer: 구조화·시각화·Marp
```

역할 전문은 `BOOTSTRAP_PROMPT.md` / `roles/<role_id>/ROLE.md`에만 둔다. 여기·PROMPT에 장문 복붙하지 않는다.

## 문서 계층 (SSOT · 중복 금지)

| 관심사 | 단일 기준 문서 | AI가 읽을 때 |
|--------|----------------|--------------|
| 진입·지도 | **이 파일** | 최초 세션·구조 변경 시 |
| 3사 동일 시작 문구 | `BOOTSTRAP_PROMPT.md` | 최초 세션 |
| 공통 실행 계약 | `PROMPT.md` | 매 세션 |
| 바인딩·쓰기 소유 | `AI_ROSTER.md` | 매 세션 |
| 패킷·handoff 상태 | `ARTIFACT_CONTRACTS.md` | handoff 생성·소비 전 |
| 역할 행동 | `roles/<role_id>/ROLE.md` + `PROMPT.md` | 자기 역할만 |
| 사용자 지시 | `To_Do.md` | 매 턴 (답변 칸) |
| 인계 큐 | `.Intermediate_Artifacts/HANDOFF.md` | 매 턴 |
| 연구 결정 로그 | `.Intermediate_Artifacts/DECISIONS.md` | 충돌 시 |
| 진행 상태 | `MILESTONES.md` · `ROADMAP.md` | 필요 시 |
| 설계 초안(역사) | `.Prompt_Engineering/*` | **읽지 않음** (구조 폐기, 운영 계약이 우선) |

**충돌 시 우선순위** → `PROMPT.md` §우선순위.

## 디렉터리

```text
Paper-Deep-Dive/
├── README.md · BOOTSTRAP_PROMPT.md · PROMPT.md
├── AI_ROSTER.md · ARTIFACT_CONTRACTS.md · AGENTS.md
├── To_Do.md
├── roles/{curator,analyst,producer}/
├── Papers/                         # curator
├── .Intermediate_Artifacts/
│   ├── papers/                     # analyst 단독
│   ├── HANDOFF.md · DECISIONS.md · MILESTONES.md · ROADMAP.md  # 공유(행 규칙)
│   └── …
└── Presentation_Marp/              # producer
```

`.Intermediate_Artifacts/` **전체**가 analyst 소유가 아니다. `papers/`만 analyst 단독. 조율 파일은 공유.

세 AI가 동일한 요청을 받아도 단독 쓰기와 공통 파일 소유권은 유지된다. 공통 정책 문서 통합은 curator가 담당하고, analyst·producer는 자신의 역할 문서만 고치거나 handoff로 제안한다.

## 사용자

볼 파일은 **`To_Do.md` 하나**.  
Canonical: `/home/user/fia_cm_haetae/Collabo_HB/Paper-Deep-Dive`
