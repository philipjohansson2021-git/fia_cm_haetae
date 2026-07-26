# ARTIFACT_CONTRACTS — 인계·패킷

다음 역할이 **추측 없이** 쓰도록, 검증된 입력만 `ready`로 넘긴다.

## 1. HANDOFF 상태

| 상태 | 소비 |
|------|------|
| `draft` | 금지 |
| `awaiting_approval` | 금지 (To_Do 승인 대기) |
| `ready` | **허용** |
| `in_progress` | 중복 착수 금지 |
| `blocked` | 금지 (재개 조건 기록) |
| `done` | 완료 |
| `cancelled` | 금지 |

스키마: `.Intermediate_Artifacts/HANDOFF.md`  
`from`/`to`는 **role_id**. 미래 계획은 `ready`로 넣지 말고 ROADMAP/MILESTONES.

## 2. curator → analyst (자산 패킷)

필수: `asset_id`, `paper_id`, 분류(대상논문/선행/참고/코드/구현/데이터/실험), 서지·출처(URL/DOI·연도·저자·라이선스·접근), 로컬 경로, 바이트, SHA-256, 열기 검증.

완료: 파일 정상·형식 일치 · 메타 대조 · **내용 해석·결론 없음**.

기록 위치: `Papers/` + `Papers/ASSET_CATALOG.md` (신규·재검증). 기존 매니페스트는 파일 대조 장부로 유지.

## 3. analyst → producer (분석 패킷)

필수: 단위 ID · 승인 상태 · 원문 위치(문서·쪽·절·Fig/표/Alg) · 배경/주장/방법/결과/기여/한계 · **원문사실 vs 저자주장 vs 해석 vs 불확실** · 승인 참조 · 청중용 출처 문구.

완료: 주장마다 근거 위치 · 필요 승인 완료 · **Marp 레이아웃 미확정**.

기록 위치: `.Intermediate_Artifacts/papers/<paper_id>/` (READING, REFS, …).

## 4. producer → 사용자 (발표 패킷)

필수: 소비 handoff/단위 ID · 슬라이드 식별(HTML 주석) · 청중 출처 · 그림 캡션 · 문법/수식/이미지 점검.

완료: 승인 밖 주장 없음 · Front matter·`$/$`·이미지 유효 · 배포본에 AI/승인 메타 없음 · 초과 시 **분할만**.

위치: `Presentation_Marp/<논문>/`.

## 5. 오류

수신 측: `blocked` + 조건 기록 → **원본 직접 수정 금지** → 송신 역할 회송.
