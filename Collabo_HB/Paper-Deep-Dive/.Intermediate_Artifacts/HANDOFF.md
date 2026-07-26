# HANDOFF

상태: `draft` | `awaiting_approval` | `ready` | `in_progress` | `blocked` | `done` | `cancelled`  
정의: `ARTIFACT_CONTRACTS.md`. **`ready`만 소비.**

```text
| id | from | to | unit | payload | gate | status | updated |
```

## 열린 항목

| id | from | to | unit | payload | gate | status | updated |
|----|------|-----|------|---------|------|--------|---------|
| HO-20260723-10 | analyst | curator | DIL-10-assets | REF-10 `[10] Correction Fault Attacks…` 로컬 PDF + 분석에 필요한 FIPS 204(표준문서) 등 **재검증** → `ASSET_CATALOG` 행 + `curator→analyst` 자산 패킷 `ready` 회신 | DIL-10 심층 선행 (v3 패킷 계약) | done | 2026-07-23 |
| HO-20260723-11 | curator | analyst | DIL-10-assets | `Papers/ASSET_CATALOG.md`: `HAETAE-FIA-REF-10`, `HAETAE-FIA-REF-01-FIPS204`, `HAETAE-FIA-REF-10-ARTIFACT` | PDF·표준 열기/메타/해시·원출처 대조, artifact ZIP 무결성 완료; 코드는 미실행 | ready | 2026-07-23 |

## 최근 완료 (레거시)

| id | from | to | unit | status | updated |
|----|------|-----|------|--------|---------|
| HO-legacy-arch | curator | analyst | M-ARCH Papers 1-deep | done | 2026-07-23 |
| HO-legacy-dil11 | analyst | producer | DIL-11-U1–U5 | done | 2026-07-22 |
| HO-legacy-dil09p | analyst | producer | DIL-09-U1–U2 | done | 2026-07-22 |

레거시 = D35 이전 단일-AI 대응. 재사용 전 근거 계약 재점검.

## 규칙

1. 송신: `draft` → 자체점검 → (승인 필요 시 `awaiting_approval`) → `ready`  
2. 수신: `ready` → `in_progress` → `done` / `blocked`  
3. 수신의 in_progress/done을 송신이 되돌리지 않음  
4. 범위 변경 시 새 행  
