# sim_code — 2026-06-28 시뮬레이션 코드 (대응기법별 정리)

이 폴더는 그날 실험에 사용한 **실제 HAETAE 전체 서명 결함주입 시뮬레이션 코드**를
**대응기법별로 정리**한 것이다. 동작하는 통합본은 `common/`, 각 대응기법의 코드 발췌·설명은
`by_countermeasure/` 에 있다.

## 구조
```
sim_code/
├─ common/                 # 동작하는 자체완결 빌드(레퍼런스 동봉)
│   ├─ sign_fi.c           #   계측 서명: 결함 훅 + baseline/IRV/Lee-Ha 로직 (CM 모드 분기)
│   ├─ campaign.c          #   캠페인(라인×모델×대응 전수) + double 비교
│   ├─ overhead.c, test2.c #   오버헤드 측정 / 불변식 단위검증
│   ├─ fi_rng.c            #   결정론적 RNG
│   ├─ haetae_src/, include/  # HAETAE 공식 레퍼런스 소스 동봉(MIT)
│   └─ Makefile
└─ by_countermeasure/      # 대응기법별 코드 발췌·설명
    ├─ baseline.c          #   무방어
    ├─ double.c            #   전체 이중연산(2회 비교, harness)
    ├─ leeha.c             #   Lee 등: sanity+시드재유도+샘플재계산+서명후검증
    └─ irv.c               #   HAETAE-IRV: M1 재계산+M2 B1노름+M3 체크섬+M4 무분기감염
```

## 빌드/실행 (common)
```bash
cd common && make
./test2       # 불변식 9/9 PASS
./campaign    # 전수 캠페인 CSV
./overhead    # 상대 오버헤드(x86)
```

## 대응기법별 적용 위치 요약
| 대응기법 | 적용 위치 | 막는 오리지널 성공지점 |
|---|---|---|
| baseline | (없음) | 없음 |
| double | 서명 전체 래퍼 | 일시적 결함 대부분 (영속 키 제외) |
| leeha | 시드/부호·난수/종료부 | 난수경로·challenge·T1·T2·key (RB 제외) |
| **irv** | z 확정 직후 | **T1·T2·RB·key (직접 키복구+거부우회)** |

결과·해석: `../fullsign_keyrecovery_report.md`, `../attack_defense_analysis.md`.
