# ASSET_CATALOG_SCHEMA — 연구자산 메타데이터 규격

새로 수집하거나 재검증하는 연구자산은 아래 필드를 기록한다. 기존 `reference-download-manifest.csv`는 파일 존재·크기 중심의 레거시 장부이며, 누락 메타데이터는 앞으로 curator가 보강한다.

| 필드 | 필수 | 설명 |
|---|---|---|
| `asset_id` | 예 | 저장소 내 불변 ID |
| `paper_id` | 예 | 관련 대상 논문 ID |
| `relation` | 예 | target, reference, prior-work, code, dataset, implementation, experiment, standard |
| `reference_no` | 조건부 | 대상 논문의 참고문헌 번호 |
| `title` | 예 | 원출처 제목 |
| `creators` | 예 | 저자 또는 기관. 확인 불가 시 `unknown` |
| `year` | 예 | 발행·릴리스 연도. 확인 불가 시 `unknown` |
| `venue_or_publisher` | 권장 | 학회·저널·기관·호스팅 조직 |
| `persistent_id` | 권장 | DOI, arXiv, IACR ePrint, 표준 번호, 커밋 SHA 등 |
| `canonical_url` | 예 | 랜딩 페이지나 공식 저장소 우선 |
| `version` | 예 | 출판본, preprint, 릴리스, 커밋 등 |
| `local_path` | 예 | 로컬 상대 경로 또는 `remote-only` |
| `bytes` | 조건부 | 로컬 파일 크기 |
| `sha256` | 조건부 | 로컬 파일 SHA-256 |
| `accessed_at` | 예 | `YYYY-MM-DD` |
| `access` | 예 | open, user-provided, institutional, restricted |
| `license` | 예 | 확인된 라이선스 또는 `unknown` |
| `verification` | 예 | verified, partial, unverified, superseded, retracted |
| `verified_against` | 예 | 검증에 쓴 원출처 |
| `notes` | 아니오 | 중복, 철회, 대체본, 파일 이상 |

## 검증 원칙

1. 검색 결과 페이지가 아니라 공식 랜딩 페이지, 출판사, 저자 공개본, 표준기관, 공식 코드 저장소를 우선한다.
2. DOI와 제목만 맞고 본문 버전이 다른 경우 `version`에 명시한다.
3. 유료벽 우회, 자격증명 공유, 라이선스 불명 자료의 재배포를 하지 않는다.
4. 코드에는 저장소 URL만 기록하지 말고 분석 대상 커밋 또는 릴리스를 고정한다.
5. 데이터셋·실험 자료는 구성, 형식, 라이선스, 재현에 필요한 버전을 함께 기록한다.
