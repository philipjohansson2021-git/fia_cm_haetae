# 2026-07-19 — 공개키 독립검증(W2) + 실서명 경로 교차검증(W3) + T1 완전복원 재현

축 A T1 물리 공격(2026-07-18, s1 768/768 완전복원)의 **방법론적 견고성**을 두 방향으로 보강하고,
완전복원을 **독립 재현**했다. 후속 논문(물리 실현성)에서 "판정이 랩 오라클/지그에 의존한다"는
반박을 제거하기 위한 산출물이다.

## 1. 무엇을 했나

1. **W2 — 공개키 독립검증 도구** (`code/verify_s1_pubkey.c`)
   복원한 `s1`을 **디바이스의 참 s1 없이, 오직 공개키(seed_A, b)만으로** 검증한다.
   HAETAE 키생성 관계 `b = ⌊a + A0·s1 + s2⌉`(공개 b=상위비트)에서, 후보 `s1'`로
   `w = a + A0·s1'`를 계산하고 `center_q(2·b1 − w)`(= 암묵 s2)가 모든 K·N 계수에서 작은지 본다.
   HAETAE 레퍼런스를 링크해 결정론 키를 재현하므로 비트정확.
   - **self-test 실측** (`results/verify_s1_pubkey_selftest.txt`):
     참 s1 잔차 **2**(PASS) · −s1 **32244**(FAIL) · 1계수 오류 **32234**(FAIL, 512/512).
     → 공개키만으로 정확·강건한 판별식임을 실증(참키 오라클 불필요).

2. **W3 — 실서명('p') 경로 교차검증 드라이버** (`code/exp7_t1_xcheck.py`)
   지그(fire_t1 재생)가 아니라 **진짜 full-sign 'p'** 2-trace로 T1 블록을 복원한다.
   거부 루프 때문에 채택 시도의 c·s를 표적하려면 **1-시도 메시지**가 필요 →
   호스트 벽시계가 아닌 **온디바이스 `scope.adc.trig_count`**(단일 c·s 창=B, K-시도≈K·B)로
   1-시도 메시지를 결정론적으로 선택. ĉ=0 슬롯이 없으면 3블록 누적 후 `verify_s1_pubkey`로 연계.
   - **3-렌즈 적대적 리뷰 후 수정 완료**(치명: block_match KeyError; 핵심: 벽시계→trig_count;
     ĉ=0 슬롯 인지). 문법·임포트 검증됨. **HW 실행 1회 대기.**

3. **T1 완전복원 독립 재현** (`results/t1_accum_reproduce_768.csv`, `..._summary.json`)
   2026-07-18과 다른 런에서 **s1 768/768** 재현: `accumulated_full=True`, `block_best=[256,256,256]`.
   결함 서명 **2개**로 전체 키 — `ext=41,421`→s1[0] `[256,0,0]`, `ext=91,672`→s1[1]+s1[2] `[0,256,256]`
   (한 글리치가 두 블록 = 반복1 후 loop-abort). 클래스 golden 351 / other 116 / mute 127.

## 2. 정직성 조건(유지)

- **인과대조 빌드** `T1_CS_ZEROINIT`(cs 사전0화) — 미수정 융합 레퍼런스는 저항(스킵=쓰레기, 07-05 T2 동형).
- **고정 nonce**(지그 재생/결정론 DRBG) — 2-trace 차분의 요건(결정론 서명에선 자연 충족).
- **판정 = 참 s1 계수단위 일치**(검증 편의) — 단, W2 도구로 **공개키만으로도** 독립 확인 가능함을 실증.

## 3. 파일 (자체완결 재현 패키지)

```
2026-07-19/
├─ README.md
├─ code/
│  ├─ Lab_HAETAE_F4_T1_AxisA.ipynb  # T1 축A 실험 노트북(EXP7-a 부트스트랩 임베드·자체완결, 실행결과 포함)
│  ├─ exp7_t1_driver.py             # 기본 T1 드라이버 (노트북이 %run -i)
│  ├─ exp7_t1_xcheck.py             # W3 실서명 'p' 경로 교차검증 (%run -i, 드라이버 뒤에 로드)
│  ├─ t1_auto.py                    # 자율 누적 드라이버(CLI; Husky free 상태에서 실행)
│  ├─ t1_accum2.json                # t1_auto.py 설정 예(3밴드 누적)
│  ├─ haetae_recover.py             # 복원 코어(NTT/디컨볼루션·디바이스 스트리밍)
│  ├─ haetae_recover_t1.py          # T1 2-trace 차분/verify_s1 (오늘 패치: None-경로 block_match)
│  ├─ export_s1_for_pubkey.py       # 복원 s1(NTT)→계수도메인 파일(verify_s1_pubkey 입력)
│  ├─ verify_s1_pubkey.c            # W2 공개키 독립검증(HAETAE 레퍼런스 링크)
│  ├─ build_verify_s1_pubkey.sh     # W2 WSL 빌드+self-test
│  ├─ verify_s1_pubkey_README.md    # W2 원리·빌드·사용·논문용 서술
│  ├─ run_aifia.bat                 # aifia conda 환경 Jupyter 실행(port 8899)
│  └─ firmware/
│     ├─ haetae_sign_cm.c           # 단일 서명함수 + VARIANT + T1 EDIT1/2(매크로 가드)
│     ├─ simpleserial-haetae.c      # CW 타겟 main(k/p/z/t/T/f/J/x/s/c)
│     ├─ Makefile                   # VARIANT / FAULT_SIM / AXISA_JIG / T1_CS_ZEROINIT 플래그
│     ├─ fault_sim.h                # 7 결함라인 FL_*
│     └─ T1_FIRMWARE_PATCH.md       # EDIT1/2 상세 + 빌드 명령
└─ results/
   ├─ t1_accum_reproduce_768.csv        # T1 완전복원 재현 런(594샷)
   ├─ t1_accum_reproduce_summary.json   # 요약(블록·파라미터·최소 결함서명 2개)
   └─ verify_s1_pubkey_selftest.txt     # W2 self-test 로그(참키 PASS/오류 FAIL)
```

- **노트북 실행 순서**: `run_aifia.bat`(aifia 커널) → `Lab_HAETAE_F4_T1_AxisA.ipynb` 위→아래.
  EXP7-a 부트스트랩(임베드) → `%run -i exp7_t1_driver.py` → (선택) `%run -i exp7_t1_xcheck.py`.
- **`code/firmware/`는 T1 관련 최상위 소스만** 담는다. 실제 빌드는 전체 HAETAE 레퍼런스
  `haetae/` 트리가 필요하며 저장소의 `firmware/simpleserial-haetae/`(또는 라이브 빌드 트리)에서 수행한다.
- **`.hex`는 저장소 관례상 미추적(빌드 산출물)** — 아래 명령으로 소스에서 빌드(§4).

## 4. 재현 방법

```bash
# 0) 펌웨어 hex 빌드 (WSL, 라이브 빌드 트리에서 — .hex 는 미추적이므로 소스에서 생성)
cd .../firmware/mcu/simpleserial-haetae     # 전체 haetae/ 레퍼런스가 있는 트리
B='PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline'
make clean $B AXISA_JIG=1 T1_CS_ZEROINIT=1 && make $B AXISA_JIG=1 T1_CS_ZEROINIT=1   # → JIG-T1-fused (누적 완전복원용)
make clean $B FAULT_SIM=1 T1_CS_ZEROINIT=1 && make $B FAULT_SIM=1 T1_CS_ZEROINIT=1   # → baseline-FSIM-T1 (W3 실서명 경로)
make clean $B FAULT_SIM=1 && make $B FAULT_SIM=1                                       # → baseline-FSIM (단계1·2)
# 각 빌드 후 cp simpleserial-haetae-CW308_STM32F4.hex haetae-<name>-CW308_STM32F4.hex
```
```bash
# W2 공개키 독립검증 (WSL, HW 불필요 — 결정론 키 재현)
wsl.exe bash -s < code/build_verify_s1_pubkey.sh    # 빌드+self-test (참키 PASS / 오류 FAIL)
./verify_s1_pubkey recovered_s1.txt                 # 실제 복원 s1 검증(있으면)
```
```python
# W3 실서명 경로 교차검증 (노트북; EXP7-a + exp7_t1_driver 로드 후, FSIM-T1 hex 필요)
%run -i exp7_t1_xcheck.py
run_t1_fullsign_xcheck(hexname='haetae-baseline-FSIM-T1-CW308_STM32F4.hex', msg_scan=32, N=1500)
```
```bash
# T1 완전복원 재현(자율판, Husky free 상태) — 2026-07-18/code 참조
python t1_auto.py t1_accum2.json
```

## 5. 논문 함의

- **W2 해소**: 복원 성공을 공개키만으로 확인 가능 → 오라클 의존 반박 제거.
- **W3(준비 완료, HW 대기)**: 지그 결과가 실서명 경로로 전이됨을 보이면 "지그=랩 가속기" 반박 제거.
- 물리 T1 완전복원은 **2회 독립 재현**으로 견고. 후속 논문에서 "실현성 연구 + IRV 동기부여"로 프레이밍.
