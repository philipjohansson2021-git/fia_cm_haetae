# HANDOFF — HAETAE FIA / T1 물리 공격 (상태·이어받기 지침)  2026-07-18

다른 세션(또는 사용자)이 **이 문서만 읽고 그대로 이어서 작업**할 수 있도록 현재 상태·경로·재현·다음
단계를 정리한다. (자동 메모리 `haetae-fia-irv-project.md`도 함께 로드됨 — 중복되면 이 문서가 최신)

---

## 0. 한 줄 요약 (현재 상태)
**축 A T1 물리 공격 완료** — 실HW 클럭글리치 다중결함 누적으로 HAETAE 비밀키 `s1`(768계수) **완전복원
(768/768)** 달성. GitHub 기록·논문 반영 초안 작성 완료. **남은 것: 논문 .tex 실제 삽입 + git push(사용자).**

정직성 3조건(반드시 유지): (a) 인과대조 빌드(`T1_CS_ZEROINIT`=cs 사전0화; **미수정 융합 레퍼런스는
저항**) (b) 고정 nonce(jig 재생/결정론 DRBG) (c) 판정=디바이스 참 s1('s' 스트림) 계수단위 정확일치.

---

## 1. 프로젝트 개요
- HAETAE(KpqC 격자 서명) **오류주입 공격 분석 + IRV(무분기 감염형 응답 무결성) 대응** 논문.
- MODE2 파라미터: `Q=64513, LN=8192(=2^13), N=256, L=4, M=L-1=3, K=2, η=1`.
- 응답: `z1[i] = y1[i] + (-1)^b·LN·(c·s1)[i]`. 비밀 s1 = **다항식 3개(각 256계수) = 768계수**(삼진 {-1,0,1}).
- 공격 지점: SEED/SIGNBIT/UNPACK/LSB(선행연구) + **T1(c·s 스킵→z≈y)·T2(+y 스킵→z=c·s1)·RB(거부스킵)**(본 논문).
- 두 축: **B**(SW 라인주입=방어자 상한) / **A**(물리 클럭글리치).

## 2. 환경 / 경로
- **conda env `aifia`**(Python 3.11, chipwhisperer 6.0.0 editable). 실행: `run_aifia.bat`(폴더서, port 8899, 커널 "Python (aifia)").
- 스크립트 직접 실행: `C:/Users/NSRSGW/miniconda3/envs/aifia/python.exe`. 한글 출력 시 `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` 필수(아니면 cp949 오류).
- **펌웨어 빌드 = WSL** (`arm-none-eabi-gcc 13.2.1`). Bash 도구의 `wsl.exe bash -lc "..."` 로 호출.
- **작업 폴더**: `C:/Users/NSRSGW/ChipWhisperer/chipwhisperer/jupyter/courses/fault_haetae_cm/`
- **펌웨어**: `C:/Users/NSRSGW/ChipWhisperer/chipwhisperer/firmware/mcu/simpleserial-haetae/`
- **GitHub 기록**: `D:/06_github_desktop/fia_cm_haetae/test/2026-07-18/` (푸시는 사용자가 직접)
- **논문**: `D:/04_project2026/paper_project/pqc_paper_haetae/pqc_haetae_fia_cm/5_paper/` (Overleaf 사용자 관리)
- **HAETAE 레퍼런스**: `D:/04_project2026/PQC_알고리즘/HAETAE-1.1.2/`

## 3. 하드웨어 / 중요 제약
- STM32F405 (CW308 소켓 + ChipWhisperer-Husky), **HSE 직결 7.37MHz**(`scope.clock.clkgen_freq=7.37e6`,
  `adc_mul=1` → 1 ADC 샘플 = 1 타깃 사이클). PSS(phase_shift_steps)=4592. GOLDEN(baseline-FSIM 서명)=`ba9f152c…`.
- **Husky는 USB 단독점유**: Jupyter 커널이 `scope`를 쥐고 있으면 자율 스크립트가 못 잡음
  (`OSError: Unable to communicate ... another process`). **자율 실행하려면 사용자가 `scope.dis()`(또는 커널
  종료)로 놓아줘야 함.** 자율 스크립트는 완료 시 `scope.dis()`로 자동 반환.

## 4. 핵심 파일 (모두 작업 폴더 `fault_haetae_cm/`)
- **복원**: `haetae_recover.py`(T2 비트정확 코어, **미수정**) / `haetae_recover_t1.py`(신규: `intt`,
  `recover_s1_from_two_traces`, `verify_s1`(NTT768+계수도메인+`block_match`+ĉ=0), `verify_two_traces`).
- **드라이버**: `t1_auto.py`(★ self-contained 자율 드라이버 — scope 직접연결·flash·prime·동일-nonce
  사전검사·스윕·per-block 누적·`scope.dis()`; config JSON 인자; `ext_bands` 다중밴드 지원) /
  `exp7_t1_driver.py`(노트북판 `%run -i`: `validate_t1_chain_sw`/`run_t1_fullsign`/`run_t1_jig`/`verify_t1_leak`).
- **노트북**: `Lab_HAETAE_F4_T1_AxisA.ipynb`(EXP7-a 부트스트랩 임베드+빌드+1·2·3단계+라이브 대시보드).
- **부트스트랩 원본**: `Lab_HAETAE_F4_EXP7_AxisA.ipynb`(축 A 세션 정의; 절대 셀[1]이 진짜 부트스트랩,
  셀[0]은 마크다운). `t2_driver.py`(07-05, standalone 부트스트랩 참고 원형; GitHub 2026-07-05/code/).
- **펌웨어**(EDIT 모두 매크로 가드 → 미정의 시 레퍼런스 바이트동일):
  - `haetae_sign_cm.c`: 응답 구간 254-317행. c·s(263-271), cneg(279-280), 융합 +y(313-314). EDIT1
    `#ifdef T1_CS_ZEROINIT`(255-260, c·s 직전 cs 사전0화). EDIT2 `#ifdef AXISA_JIG`(globals j_s1/j_c/j_b
    +prime 저장 + `haetae_axisa_fire_t1()` = 저장 nonce로 c·s 재실행).
  - `simpleserial-haetae.c`: `cmd_jig` `'J' 0`=prime/`1`=fire(+y)/`2`=fire_t1(c·s). 'x/s/c' 스트림, 'T' 트리거, 'f' SW결함.
  - `Makefile`: `T1_CS_ZEROINIT=1`, `AXISA_JIG=1`(→FAULT_SIM 자동), `FAULT_SIM=1` 플래그.
  - `T1_FIRMWARE_PATCH.md`: EDIT 상세 + 빌드 명령.
- **빌드된 hex**(펌웨어 폴더): `haetae-JIG-T1-fused-CW308_STM32F4.hex`(AXISA_JIG=1 T1_CS_ZEROINIT=1, 완전복원용),
  `haetae-baseline-FSIM-T1`(FAULT_SIM=1 T1_CS_ZEROINIT=1), `haetae-baseline-FSIM`(미수정, 단계1·2).

## 5. T1 공격 원리 (요약)
- `c·s1`은 다항식 3개를 **3-반복 루프**(반복당 pointwise 256곱 + 역NTT ~1024나비+256정규화 ≈ 50k사이클)로 계산.
- 글리치가 **한 반복(다항식 1개) 계산을 통째로 스킵** → cs 사전0화(EDIT1) 덕에 그 블록=0 → 2-trace 차분
  `z_clean−z_fault`에서 그 블록만 깨끗한 `LN·c·s1[j]` → 공개 c로 NTT 역변환 → s1[j] 복원(=256/768=33%).
- 세 반복은 서로 다른 글리치 지연(ext)에서 표적 → 블록별 결함서명을 누적 → 768/768.

## 6. 달성 결과 (2026-07-18) — GitHub results/*.json 참조
| 단계 | 결과 | 파일 |
|---|---|---|
| 1 복원체인(글리치X, SW모델) | s1 **768/768** | t1_stage1_validation.json |
| 2 단일글리치 재현 부분누설 | **33%(28히트)**, ext 41,439–41,991 | t1_denseband_reproduce.json |
| 3 3블록 도달(전구간 스캔) | 밴드 ~41.9k/92.3k/143.1k | t1_autoscan_3bands.json |
| 4 누적 완전복원 | **768/768**, `accumulated_full=True`, 결함서명 2개 | t1_FULL_recovery_768.json |
- 완전복원 조합: `ext=41,421`→s1[0] 256/256; `ext=91,670`→s1[1]+s1[2] 512/768(한 글리치 두 블록, 66.7%).
- 글리치 파라미터: **width 55–68, offset 12–14, repeat 2** (Husky clock_xor, ext_single).

## 7. 재현 방법
```bash
# (WSL) hex 빌드 — 이미 빌드돼 있으면 생략
cd /mnt/c/Users/NSRSGW/ChipWhisperer/chipwhisperer/firmware/mcu/simpleserial-haetae
B='PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline'
make clean $B AXISA_JIG=1 T1_CS_ZEROINIT=1 && make $B AXISA_JIG=1 T1_CS_ZEROINIT=1
cp simpleserial-haetae-CW308_STM32F4.hex haetae-JIG-T1-fused-CW308_STM32F4.hex
```
```bash
# (자율 실행 — Husky가 free여야: 커널 scope.dis()) 완전복원 재현
cd C:/Users/NSRSGW/ChipWhisperer/chipwhisperer/jupyter/courses/fault_haetae_cm
PYTHONUTF8=1 python t1_auto.py t1_accum2.json    # t1_accum2.json: ext_bands 3밴드, N=900
# → RESULT ... accumulated_full: true  이면 768/768. 로그: t1_accum2_summary.json / _progress.txt
```
노트북 경로: `run_aifia.bat` → `Lab_HAETAE_F4_T1_AxisA.ipynb` 위→아래(EXP7-a 후 `TRIG_POINT=FL['CS']`).

## 8. 알려진 함정 (디버깅에서 확정)
- **`scope.adc.trig_count`(WIN) 오측정**: c·s WIN이 205M 등 거대값으로 잘못 나옴(실제 ~192k, 밴드 ~50k
  간격). → 드라이버는 `E_MAX` 클램프(`win if 50<win<300000 else 60000`) 또는 `ext_bands` 수동 지정.
- **golden 샷 z1-read 금지**: golden(=prime 다이제스트)은 z1(64청크 시리얼) 읽지 말 것 → 3.3s→0.3s.
- **jig fire는 capture-first**(fire ~26ms라 read 전에 capture) + read timeout 1000ms.
- **mute(크래시)마다 reprime(~8s full sign)** 필요(jig 상태 소실). mute율 ~20%가 시간 대부분.
- **글리치 모듈 enable 전 `set_glitch` 금지**(WIN 측정·prime 사전검사는 글리치 미사용).
- **노트북 빌더**: EXP7_AxisA 절대셀[0]은 마크다운(코드로 임베드 시 SyntaxError) → 마커로 코드셀 추출.

## 9. 다음 단계 (미완 / 이어서 할 일)
1. **논문 .tex 반영** (사용자 Overleaf; 초안 `5_paper/sections/T1_physical_writeup_ko.md` = 이 폴더
   `paper/T1_physical_writeup_ko.md`): (A)새 소절 `\subsection{물리 클럭 글리치를 통한 T1 공격 실증}`
   삽입, (B)`§논의 및 한계`의 "오류 모델의 현실성" 항목을 물리실현 반영본으로 교체, (C)초록·서론 한 줄.
   ⚠ 초안이 참조하는 `\label{subsec:phys-t2-resist}`(07-05 T2 물리내성 소절)가 없으면 신설·라벨 연결.
2. **git push**(사용자): `test/2026-07-18/` + `test/README.md`.
3. (선택 확장) **미수정 레퍼런스 T1 저항 정량화**(T1_CS_ZEROINIT 없이 → 쓰레기/저항 대조표),
   **대응기법(irv/leeha/double)에서 T1 물리 커버리지**(현재 커버리지는 축 B/SW 기준),
   **full-sign 경로 완전복원 교차검증**(jig 아닌 'p', diff%LN 게이트).
4. (분석) 왜 ext=91,670이 두 블록 동시 스킵인지(루프 iter1 후 종료) 미세 규명 — 논문 부록용 선택.

## 10. 판정·복원 신뢰성 (재확인용)
- `verify_s1(rec_s1ntt, true_s1ntt, c)`: NTT도메인 768 정확일치(권위, (-1)^b ± 흡수) + `block_match`
  [s1[0],s1[1],s1[2]] 각 256 + `intt` 계수도메인({-1,0,1}) + ĉ=0 슬롯 계상. 합성 자기검증 통과.
- 완전복원 = `block_cov=[True,True,True]`(각 블록 ≥254/256 도달) → `accumulated_full`.
- 차분 무결성 게이트: `diff%LN==0`(y 정확상쇄 + cs 깨끗제거). 미충족 시 'other'(쓰레기).
