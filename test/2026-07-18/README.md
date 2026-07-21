# 2026-07-18 — 축 A T1(c·s 스킵 → z=y) 2-서명 출력 차분: 실HW 클럭글리치로 s1 완전복원(768/768)

STM32F4(CW308 + Husky, HSE 직결 7.37MHz)에서 **T1** 오류(챌린지 곱 `c·s1` 스킵 → 결함 응답 `z=y1`(nonce))를
이용한 **2-서명 출력 차분 공격**을 설계·구현하고, **실제 클럭글리치 다중결함 누적으로 HAETAE 비밀키
`s1`(768계수) 전체를 물리 복원**한 날.

> **★ 최종 결과**: 실HW 클럭글리치로 **`s1` = 768/768 완전복원**. 결함 서명 2개
> (글리치 `ext=41,421`→`s1[0]`, `ext=91,670`→`s1[1]+s1[2]`)의 2-서명 출력 차분을 **블록별 누적** →
> 세 비밀 다항식 전부를 **디바이스 참 키와 비트단위 정확 일치** 복원(`accumulated_full=True`).
>
> **정직성 3조건**: (a) **인과 대조 빌드**(`T1_CS_ZEROINIT`: `c·s` 직전 `cs` 사전 0화). 미수정 융합
> 레퍼런스는 저항(cs 미초기화 → 스킵=쓰레기, 2026-07-05 T2 내성과 동형); EDIT1은 물리 실현을 여는
> 인과 대조(=twopass↔T2). (b) **고정 nonce**(fast-jig 재생 / 결정론 DRBG). (c) 판정 = 디바이스 참
> `s1`(‘s’ 스트림)과 **계수단위 정확 일치**(프록시 아님).

---

## 무엇을 했나

1. **어셈블리 확정**(ELF objdump): 융합 `+y`는 단일 명령 `add.w r4,r4,r5,lsl#13`(`z1[i]=y1[i]+LN·cs1[i]`, int32,
   LN=2^13). "스킵"은 z=cs가 아니라 z=y(=T1) 또는 쓰레기 → **T1(z=y) 2-서명 출력 차분**을 공격 경로로 채택.
2. **T1 복원 모듈**(`haetae_recover_t1.py`, 기존 비트정확 `haetae_recover.py` 미수정 재사용):
   `recover_s1_from_two_traces`(diff→기존 T2 역변환) + `verify_s1`(NTT 768 정확일치 + `intt` 계수도메인
   + `block_match` 블록 식별 + ĉ=0 슬롯 계상). 합성 자기검증 통과.
3. **자율 드라이버 `t1_auto.py`**(self-contained, scope 직접 연결·flash·prime·동일-nonce 사전검사·스윕·
   per-block 누적·`scope.dis()` 반환) — 노트북 없이 커맨드라인 자율 실행. `exp7_t1_driver.py`(노트북판) 병행.
4. **펌웨어 EDIT(모두 매크로 가드 → 레퍼런스 기본 빌드 바이트동일)**:
   `T1_CS_ZEROINIT`(c·s 직전 cs 사전 0화 → 물리 스킵이 z=y), `AXISA_JIG` fire_t1(저장 nonce로 c·s 재실행,
   `'J' 2`). hex: `haetae-JIG-T1-fused`(EDIT1+2). 자세히는 `code/T1_FIRMWARE_PATCH.md`.
5. **자체완결 노트북** `Lab_HAETAE_F4_T1_AxisA.ipynb`(EXP7-a 임베드 + 빌드 + 1·2·3단계 + 라이브 모니터).

---

## 단계별 결과

| 단계 | 내용 | 결과 | 파일 |
|---|---|---|---|
| **1** 복원체인 | 글리치 없이 디바이스 SW T1 모델(FL_CS: c·s=0→z=y)로 z_clean−z_fault 차분 | **s1 768/768** (계수도메인 {-1,0,1}, msg#0 즉시) | `t1_stage1_validation.json` |
| **2** 단일글리치 부분누설 | 물리 글리치가 c·s 한 다항식 clean 스킵 | **재현 가능 33%**(28히트, ext 41,439~41,991, 33.3%→30.2%) | `t1_denseband_reproduce.json`, `t1_jig_denseband_41-42k.csv` |
| **3** 3블록 도달 | 전-c·s 자율스캔(N=1200, ext 0~192,247) | 세 다항식 각 **독립 ext 밴드**(~41.9k / 92.3k / 143.1k = c·s 3반복) | `t1_autoscan_3bands.json`, `t1_autoscan_fullcs.csv` |
| **4** 누적 완전복원 | 3밴드 dense 누적 | **s1 768/768**, `block_best=[256,256,256]`, `accumulated_full=True`, 결함서명 2개 | `t1_FULL_recovery_768.json`, `t1_accum_full768.csv` |

**단일 최고 샷**: `ext=91,670`에서 **한 글리치가 두 블록(s1[1]+s1[2]) 동시 스킵 = 512/768(66.7%)**
(루프가 iter1 후 종료). `ext=41,421`에서 s1[0](256/256). 둘 누적 = 768/768.

---

## 메커니즘 — 왜 다항식(블록) 단위인가

`c·s1`은 **다항식 3개(s1[0..2], 각 256계수)** 를 **3-반복 루프**로 계산(반복당 pointwise 256 + 역NTT).
전체 c·s ≈ 192k 사이클, 반복당 ~50k → 밴드 3개가 **~50k 등간격**. 글리치가 **한 반복(다항식 하나)의 계산을
통째로 스킵**하면 그 블록이 사전0화(EDIT1) 0으로 남아 차분에서 **깨끗이 복원**(=256/768=33%). 반복별로
다른 ext를 때려 **블록을 모으면 768/768**.

응답 산술: `z1[i] = y1[i] + (-1)^b·LN·(c·s1)[i]`. c·s(NTT 곱, 3반복) → cneg((-1)^b) → +y(LN 융합덧셈).

---

## 정직성 / 한계

- **인과 대조 빌드**: 물리 클린 스킵은 `T1_CS_ZEROINIT`(cs 사전 0화) 빌드에서 성립. **미수정 융합
  레퍼런스는 저항**(cs 미초기화 → 스킵=쓰레기, z≠y) — 2026-07-05 T2 내성과 동형. EDIT1은 물리 실현을
  여는 인과 대조(=T2의 twopass 대조군).
- **고정 nonce**: 2-서명 출력 차분은 두 서명 출력의 y가 동일해야 성립. fast-jig가 저장 nonce를 재생(결정론
  DRBG). 랩 조건.
- **지상진실 판정**: 복원값 vs 디바이스 참 s1(‘s’ 스트림) 계수단위 정확 일치. 768/768은 프록시 아닌 실측.

## 논문 함의

T1의 **물리 실현성이 end-to-end로 확립**: 복원식 실증(단계1) → 재현 부분누설(단계2) → 누적 완전복원
(단계4). detect-and-abort 대응이 skip 결함에 우회됨을 보여 **IRV(무분기 감염형 응답 무결성)** 대응의
동기를 강화한다. 미수정 레퍼런스 저항은 구현 속성(융합·cs 미초기화)이므로, 재컴파일·다른 구현에서
공격이 열릴 수 있어 대응이 필요하다.

## 파일

```
code/
├─ Lab_HAETAE_F4_T1_AxisA.ipynb   자체완결 T1 노트북(EXP7-a 임베드+빌드+1·2·3단계+라이브 모니터)
├─ t1_auto.py                     자율 드라이버(scope 직접 연결, per-block 누적, ext_bands)  ※ 완전복원 실행체
├─ exp7_t1_driver.py              노트북판 드라이버(validate/fullsign/jig/verify_t1_leak)
├─ haetae_recover_t1.py           T1 차분 복원 + s값 검증(intt·block_match)  ※ 신규
├─ haetae_recover.py              T2 비트정확 복원 코어(재사용, 미수정)
├─ T1_FIRMWARE_PATCH.md           펌웨어 EDIT1/2 + 빌드 + 노트북 사용법
├─ run_aifia.bat                  aifia + ChipWhisperer Jupyter 실행
└─ firmware/                      EDIT1+2 적용 소스(매크로 가드; haetae_sign_cm.c·simpleserial-haetae.c·fault_sim.h·makefile)
results/
├─ t1_FULL_recovery_768.json      ★ 최종 완전복원(768/768) 요약
├─ t1_stage1_validation.json      단계1 복원체인 검증(768/768, SW모델)
├─ t1_denseband_reproduce.json    단계2 재현 33%(28히트)
├─ t1_autoscan_3bands.json        단계3 3블록 도달(밴드 3개)
├─ t1_accumulation.json           단계4 누적(중간: block0=256)
├─ t1_accum_full768.csv/_summary  최종 누적 로그(768/768)
└─ (그 외 스윕 CSV: t1_jig_denseband_41-42k, t1_autoscan_fullcs, t1_accum_3band ...)
figures/
└─ fig_t1_jig_map.png             축 A c·s 스윕 맵
```

> 재현: `code/`를 aifia 환경에 두고 `haetae-JIG-T1-fused` hex(AXISA_JIG=1 T1_CS_ZEROINIT=1) 빌드 후
> `python t1_auto.py t1_accum2.json`(3밴드 누적) 또는 노트북 위→아래.
> 완전복원은 인과대조 빌드(EDIT1)+고정nonce(jig) 조건. 미수정 레퍼런스는 저항.
