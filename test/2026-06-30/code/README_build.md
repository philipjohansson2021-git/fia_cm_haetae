# 재현 가이드 — STM32F4 HAETAE 결함주입 (펌웨어 + Husky 호스트)

이 폴더로 2026-06-30 실험을 재현한다. 펌웨어 4파일 + HAETAE 레퍼런스 소스로 빌드하고,
ChipWhisperer-Husky + CW308 STM32F4 에서 노트북으로 실행한다.

## 0. 구성
```
code/
├─ firmware/
│  ├─ simpleserial-haetae.c   타겟 main (k/p/z/t + FAULT_SIM: f/x/s/c)
│  ├─ haetae_sign_cm.c        전체 서명 + 4변형(VARIANT 매크로) + 결함훅(FAULT_SIM)
│  ├─ fault_sim.h             결함 라인 ID(FL_*) + 플래그
│  └─ makefile                VARIANT=baseline|double|leeha|irv, FAULT_SIM, MCU_CLK
├─ haetae_recover.py          T2 직접복원(z1→s1) + 디바이스 스트리밍 유틸
├─ docs/
│  └─ IRV_design_notes.md     HAETAE-IRV 설계 상세(M1~M4 메커니즘·B1<B2 통찰·이전버전 diff)
├─ Lab_HAETAE_F4_FullSign_v1_1_goodresult.ipynb   [보관용] SETUP→BUILD→SMOKE→EXP1..6 (축 B, 결과 포함)
└─ Lab_HAETAE_F4_FullSign_v1.ipynb                [작업본] 위 + EXP7(축 A 하드웨어 클럭글리치 캠페인)
```

> **두 노트북 차이**: `_v1_1_goodresult`는 EXP1~6(축 B=FAULT_SIM 결정론 라인주입, 대응기법 공정비교)의
> 확정 결과 보관본. `_v1`은 거기에 EXP7(축 A=실제 클럭글리치로 T2 실재성 검증) 셀을 추가한 작업본이며,
> 축 A 캠페인은 진행 중(결과 추후 갱신).

## 1. 하드웨어
- ChipWhisperer-Husky + CW308 UFO + **STM32F4(STM32F405, 192KB SRAM)** 타겟.
- 클럭: **HSE 직결**(CW HS2 외부클럭 7.37MHz). `scope.io.hs2='clkgen'`, `scope.clock.clkgen_freq=7.37e6`.

## 2. 소스 배치 (ChipWhisperer 펌웨어 트리)
ChipWhisperer 설치본의 `firmware/mcu/simpleserial-haetae/` 에 배치:
1. `firmware/`의 4파일(main·sign_cm·fault_sim.h·makefile)을 그 폴더에 복사.
2. 같은 폴더의 `haetae/` 에 HAETAE **공식 레퍼런스 소스**(reference_implementation의 src/*.c + include/)를 둔다.
   - 필요 소스: decompose, encoding, fft, fixpoint, ntt, packing, poly, polyvec, polymat, polyfix,
     reduce, sampler, fips202, symmetric-shake + 헤더, 그리고 **keypair/verify 제공용** `sign_baseline.c`,
     결정론 RNG `randombytes_drbg.c`. (makefile SRC 참고.)
   - 본 repo `docs/haetae_reference/` 또는 공식 HAETAE 저장소에서 가져온다.

## 3. F4 HAL 서브모듈 (최초 1회)
F4 HAL은 `chipwhisperer-fw-extra` 서브모듈에 있음(미초기화 시 빌드 실패):
```bash
cd <chipwhisperer>
git submodule update --init firmware/mcu/hal/chipwhisperer-fw-extra
# 확인: firmware/mcu/hal/chipwhisperer-fw-extra/stm32f4/Makefile.stm32f4
```
※ 내부 168MHz(`MCU_CLK=INT`)는 HAL flash wait-state 버그로 미사용 — **HSE 직결(기본)** 만 사용.

## 4. 빌드 (변형별)
```bash
cd firmware/mcu/simpleserial-haetae
# 무결함(오버헤드/타이밍용):    VARIANT = baseline | double | leeha | irv
make clean PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=irv
make       PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=irv
# 결함주입 실험용: 위에 FAULT_SIM=1 추가
make ... VARIANT=irv FAULT_SIM=1
```
출력 `simpleserial-haetae-CW308_STM32F4.hex` 를 변형/모드별로 파일명 바꿔 보관.

## 5. 펌웨어 커맨드 (SimpleSerial v1.1)
| cmd | in | 설명 |
|---|---|---|
| `e` | 0B | echo(통신 진단) → 0xA0..0xAF |
| `k` | 0B | 결정론 키 재생성 |
| `p` | 16B | 입력=메시지로 1회 서명 → 'r' 16B = 서명 SHAKE 다이제스트 |
| `t` | 16B | 서명 1회 DWT 사이클 → 'r' 4B |
| `f` | 3B | (FAULT_SIM) [라인 FL_*, oneshot, checkskip] 결함 설정 |
| `x`/`s`/`c` | 1B | (FAULT_SIM) z1 / 참 s1(NTT) / 챌린지 c 64B 청크 스트리밍 (T2 복원용) |

결함 라인(FL_*): 1=SEED 2=SIGNBIT 3=UNPACK 4=LSB 5=CS(T1) 6=ADDY(T2) 7=REJECT(RB).

## 6. 실행 (노트북)
`Lab_HAETAE_F4_FullSign_v1_1_goodresult.ipynb` 를 ChipWhisperer Jupyter(`jupyter/courses/fault201/`)에 두고
`haetae_recover.py` 와 같은 폴더에 둔 뒤 **위에서부터** 실행:
- SETUP(클럭+함수 정의) → BUILD(8 hex) → SMOKE(GOLDEN) →
  EXP1(T2 직접추출) · EXP2(커버리지) · EXP3(재현율) · EXP4(2차결함) · EXP5(오버헤드) · EXP6(연산시간).
- 7.37MHz라 서명 1회 수 초; 거부반복 많은 키는 더 느림(EXP3는 M 낮춰 단축).

**축 A (EXP7, `Lab_HAETAE_F4_FullSign_v1.ipynb` 전용):** 실제 클럭글리치로 T2 실재성 검증.
- EXP7-a 글리치 셋업(baseline+FSIM, `FL_NONE`으로 SW결함 OFF, `clock_xor`, 트리거윈도우 측정) →
  EXP7-b 좁은 격자 스윕(success=LEAK_T2 다이제스트로 분류, `glitch_log.csv`) →
  EXP7-c success 시 `attack_recover`로 실제 s1 복원 + `fig_glitch_map`.
- 전체서명 1회 ~8초 → 좁은 격자 집중 스윕 권장. **(진행 중 — 결과 추후 갱신)**

## 7. 변형 요약
| VARIANT | 대응 |
|---|---|
| baseline | 무방어 |
| double | 전체 이중연산(2회 비교, main) |
| leeha | Lee-Ha 재구현: 서명후검증 + 정상성 + 시드재유도 + 부분이중연산(채택 1회) |
| irv | HAETAE-IRV: M1(c·s재계산)+M2(B0/B1 노름재검사)+M1b(시드정상성)+M1c(부호/논스 재유도)+M1'(검증, main)+M4(무분기 감염) |

> 결과·표는 상위 `../README.md` 및 CSV(coverage/success_rate/2ndorder/overhead/timing) 참조.
