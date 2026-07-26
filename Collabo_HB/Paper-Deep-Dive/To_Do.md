# To_Do.md — 사용자↔AI 단일 접점

Canonical: `/home/user/fia_cm_haetae/Collabo_HB/Paper-Deep-Dive/To_Do.md`
채팅 **`계속`** = 아래 **답변 칸**만 지시로 사용.

---

## 연구환경

| role_id | 서비스 | 책임 한 줄 |
|---------|--------|------------|
| `curator` | Codex | 수집·검증·`Papers/` |
| `analyst` | Grok | 심층 분석·해석 |
| `producer` | Agy | Marp·스토리 |

---

## 지금 상태

| | |
|--|--|
| 부트스트랩 | **완료** (사용자 `부트스트랩 완료`) · M0 done |
| 3-AI | curator=Codex · analyst=Grok · producer=Agy 확정 |
| analyst | DIL-10 **미착수** — 선행 2건 대기 |
| ready handoff (analyst 소비) | `HO-20260723-11` — DIL-10 자산 3건 |

---

## 이번 턴에 한 일

- 답변 칸/채팅: **`부트스트랩 완료`** 반영
- M0 → done · 다음 게이트 전환
- HANDOFF: `analyst → curator` DIL-10 자산 재검증 요청 (`ready`)
- curator: DIL-10 논문·FIPS 204·공식 재현 아티팩트 검증 및 카탈로그 등록
- HANDOFF: 요청 `HO-20260723-10` 완료 → 응답 `HO-20260723-11` ready

---

## 지금 할 일 (사용자) — 1건

### ☐ [analyst] sparse-c-NTT 한 줄 반영 검토

**배경:** Dilithium deep-dive 중, *Sign_internal* 에서 *NTT* 가 불리는 곳 (FIPS 204 Alg 7).
전용 슬라이드 1장은 과하다고 보아 **삭제**했고, 아래 **한 줄**만 NTT 호출 표 슬라이드 하단에 유지한 상태입니다.

**유지 문장(안):**
> L16 *SampleInBall* 로 $c$ 가 sparse 이어도, FIPS 204는 L17에서 $\mathrm{NTT}(c)$ 를 생략하지 않는다.

| 답변 칸 | 의미 |
|---------|------|
| **`승인`** / **`작업 계속`** | 한 줄 OK → analyst가 DIL-10 심층 착수 |
| **`수정: …`** | 문장·위치 수정 |
| **`삭제`** | 해당 한 줄도 제거 |

> **참고 (응답 불필요):** curator 자산 패킷은 `HO-20260723-11`로 준비 완료되었습니다. 현재 남은 선행 조건은 위 사용자 게이트 하나입니다.

---

## 다음에 올 일 (응답 불필요)

1. `[analyst]` 사용자 승인 후 `HO-20260723-11` 소비 → DIL-10 심층 1단위
2. `[producer]` 승인된 분석 `ready`만 Marp

---

## 최근 완료

- 사용자: 부트스트랩 완료
- curator: DIL-10 자산 패킷 ready
- D35–D38: 3-AI·SSOT·통합 규칙

---

## 사용자 답변 칸

```
(여기에 기입)
```
