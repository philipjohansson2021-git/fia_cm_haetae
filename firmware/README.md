# HAETAE 오류주입 실험 펌웨어

HAETAE 서명에 대한 오류주입공격(FIA)과 경량 대응기법(IRV) 실험에 사용한 ChipWhisperer 타겟 펌웨어입니다.
타겟: **CW308 + STM32F405**(Cortex-M4, 축 A 하드웨어 클럭글리치) 및 STM32F303(초기 F3 라인).

단일 서명 함수(`simpleserial-haetae/haetae_sign_cm.c`)가 **컴파일타임 매크로**로 4가지 대응 변형을 분기합니다.
파일 하나만 교체하는 방식이 아니라 프로젝트 폴더 전체로 빌드합니다(HAETAE 레퍼런스 소스 16개 포함).

## 4가지 변형 (VARIANT)

| VARIANT | 매크로 | 내용 |
|---|---|---|
| `baseline` | (없음) | 무방어 — 레퍼런스 그대로. 공격 대상. |
| `double`   | `-DHAETAE_VARIANT_DOUBLE` | 전체 이중 연산(main에서 2회 서명·비교). 포괄적이나 서명시간 2배, 2차 오류에 우회됨. |
| `leeha`    | `-DHAETAE_VARIANT_LEEHA`  | 선행연구(Lee 등, JKIISC 2026) 대응 재구현 — 서명후검증·정상성·부분이중. 거부우회(RB) 미차단. |
| `irv`      | `-DHAETAE_VARIANT_IRV`    | **제안 기법 IRV** — 무분기 감염형 무결성 보호. M1(c·s 재계산)+M2(서명경계 노름 재검사)+M3(키 체크섬)을 잔차 δ에 누적 후, δ≠0이면 서명을 PRF로 난수화(감염). 비교 분기가 없어 2차 분기-스킵에 내성. |

`twopass`(`-DHAETAE_VARIANT_TWOPASS`, 비융합 2단계 +y)는 물리 clean-T2 실현성 인과 대조용 보조 변형입니다.

## 빌드 (WSL: arm-none-eabi-gcc + GnuWin32 make)

Jupyter 셀 `%%bash` 또는 WSL 셸에서 각 변형을 빌드하고 결과 hex를 이름 붙여 보관합니다:

```bash
cd simpleserial-haetae
for V in baseline double leeha irv; do
  make clean PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=$V
  make       PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=$V
  cp simpleserial-haetae-CW308_STM32F4.hex ../prebuilt/haetae-$V-CW308_STM32F4.hex
done
```

- `CRYPTO_TARGET=NONE` (HAETAE 자체 구현이라 AES 예제와 달리 NONE), `SS_VER=SS_VER_1_1`.
- **축 B**(소프트웨어 라인 결함주입, 대응기법 공정 비교): 위 명령에 `FAULT_SIM=1` 추가 → `haetae-<V>-FSIM-*.hex`.
- **축 A**(하드웨어 클럭글리치 지그): `AXISA_JIG=1` 추가(FAULT_SIM 자동 포함). `'J'` 지그 커맨드:
  `0`=prime(정상 서명 1회+상태 저장), `1`=fire(+y 재실행=T2 표적), `2`=fire_t1(c·s 재실행=T1 표적).
- **축 A T1(c·s 스킵 → z=y, 2026-07-18 실증)**: `T1_CS_ZEROINIT=1`로 c·s 직전 `cs` 버퍼를 사전 0화하면
  물리 loop-abort 스킵이 쓰레기가 아니라 `z=y`(=해당 다항식 블록 제거)를 내어, 2-trace 차분으로 `s1`
  복원이 성립한다(인과 대조 빌드). **미수정 레퍼런스는 이 초기화가 없어 저항**하므로, 매크로 가드로
  기본 빌드는 바이트동일이다.
  ```bash
  make clean PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline AXISA_JIG=1 T1_CS_ZEROINIT=1
  make       PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline AXISA_JIG=1 T1_CS_ZEROINIT=1
  cp simpleserial-haetae-CW308_STM32F4.hex ../prebuilt/haetae-JIG-T1-fused-CW308_STM32F4.hex
  ```
  실험·결과·재현은 `../../test/2026-07-18/`(HANDOFF.md, results/, code/) 참조.
- 상세 빌드/호스트 프로토콜은 `simpleserial-haetae/BUILD.md` 참조.

## 구성

```
firmware/
└─ simpleserial-haetae/
   ├─ makefile                VARIANT/FAULT_SIM/AXISA_JIG 선택
   ├─ simpleserial-haetae.c   타겟 main + simpleserial v1.1 커맨드(k/p/c, 스트림 x/s/c, J/C 지그)
   ├─ haetae_sign_cm.c        ★ 컴파일되는 4-변형 서명 (VARIANT 매크로로 분기). infect_sig() = M4 무분기 감염 마스킹
   ├─ fault_sim.h             축 B 라인 결함주입 훅
   ├─ BUILD.md                빌드·호스트 프로토콜 상세
   ├─ haetae/                 HAETAE 레퍼런스 소스 + include/ (poly/ntt/sampler/packing/…)
   │  ├─ randombytes_drbg.c   고정 시드 결정론 DRBG (baseline↔대응 1:1 비교용, 실험 전용)
   │  ├─ sign_baseline.c      레퍼런스 keypair/verify 제공원
   │  └─ sign_irv.c           독립형 IRV 참조 구현 (빌드 미포함 — 실제 빌드는 haetae_sign_cm.c)
   └─ prebuilt/               사전 빌드 hex (변형별, +FSIM 축B, +INT 클럭, +JIG-T1-fused/FSIM-T1 축A T1)
```

## 참고

- **감염 마스크 신선도**: `infect_sig`는 PRF를 `sk_seed ‖ δ ‖ mu`(메시지 해시)로 키잉합니다. 메시지 결합으로 동일 δ가 다른 메시지에서 다른 마스크를 내어, 두 감염 출력의 XOR로 마스크가 상쇄되지 않습니다.
- **결정론 DRBG**는 의도적으로 모든 서명이 동일 키·동일 nonce를 쓰게 하여 baseline과 대응기법을 1:1 대조하고 골든↔결함 서명을 정확히 비교하기 위한 **실험 전용** 설정입니다. 운영에는 하드웨어 RNG로 교체해야 합니다.
