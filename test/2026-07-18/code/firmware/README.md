# 2026-07-18 T1 실험 펌웨어 (수정 파일 스냅샷)

이 폴더는 축 A T1(c·s 스킵→z=y) 실험에 **수정한 핵심 파일**과 **빌드된 hex**입니다.
전체 빌드 가능한 캐노니컬 트리(레퍼런스 소스·include 포함)는 repo `firmware/simpleserial-haetae/`에 있습니다.

## 파일
- `haetae_sign_cm.c` — 응답 서명. **EDIT1**(`#ifdef T1_CS_ZEROINIT`: c·s 직전 cs 사전 0화),
  **EDIT2**(`#ifdef AXISA_JIG`: globals j_s1/j_c/j_b + prime 저장 + `haetae_axisa_fire_t1()` c·s 재실행).
- `simpleserial-haetae.c` — `cmd_jig`에 `'J' 2`=fire_t1(c·s) 분기 + extern.
- `fault_sim.h` — FL_* 결함지점(FL_CS=5, FL_ADDY=6) + 트리거/결함 훅.
- `makefile` — `T1_CS_ZEROINIT=1`, `AXISA_JIG=1`, `FAULT_SIM=1` 플래그.
- `haetae-JIG-T1-fused-CW308_STM32F4.hex` — **완전복원 실험에 사용한 hex**(AXISA_JIG=1 T1_CS_ZEROINIT=1).
- `haetae-baseline-FSIM-T1-CW308_STM32F4.hex` — full-sign 교차검증용(FAULT_SIM=1 T1_CS_ZEROINIT=1).

## 빌드 (WSL)
```bash
cd <repo>/firmware/simpleserial-haetae   # 또는 라이브 빌드트리
make clean PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline AXISA_JIG=1 T1_CS_ZEROINIT=1
make       PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline AXISA_JIG=1 T1_CS_ZEROINIT=1
cp simpleserial-haetae-CW308_STM32F4.hex haetae-JIG-T1-fused-CW308_STM32F4.hex
```
> 모든 EDIT는 매크로 가드 → 플래그 미지정 시 레퍼런스 기본 빌드와 바이트동일(미수정 레퍼런스는 물리 T1 저항).
> 자세히는 `../T1_FIRMWARE_PATCH.md`, 실험 전체는 `../../HANDOFF.md`.
