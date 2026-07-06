# simpleserial-haetae — ChipWhisperer 빌드 안내

HAETAE 오류주입 실험용 CW 타겟. **단일 .c 교체가 아니라 이 프로젝트 폴더 전체로 빌드**합니다
(HAETAE는 소스가 16개라 AES 예제처럼 파일 하나만 바꾸는 방식이 아닙니다). baseline(무방어)과
irv(HAETAE-IRV)를 `VARIANT`로 선택합니다.

## 폴더 구성
```
simpleserial-haetae/
├─ makefile                  CW 빌드 (VARIANT로 baseline/irv 선택)
├─ simpleserial-haetae.c     타겟 main (k/p/c 커맨드, c·s 구간 트리거)
└─ haetae/
   ├─ include/*.h            HAETAE 레퍼런스 헤더
   ├─ *.c                    HAETAE 레퍼런스 소스 (poly/ntt/sampler/…)
   ├─ sign_baseline.c        무방어 서명 (CW 트리거 훅 포함)
   ├─ sign_irv.c             HAETAE-IRV 서명 (대응기법 + 트리거 훅)
   └─ randombytes_drbg.c     결정론적 DRBG (베어메탈 RNG, 재현성용)
```

## 빌드 (Jupyter 노트북 셀 — fault101 예제와 동일 패턴)
```python
PLATFORM = "CW308_STM32F3"      # = CWLITEARM
SS_VER   = "SS_VER_1_1"         # 이 타겟의 main은 v1.1 API 기준
```
```bash
%%bash -s "$PLATFORM" "$SS_VER"
cd ../../../firmware/mcu/simpleserial-haetae
make clean PLATFORM=$1 CRYPTO_TARGET=NONE SS_VER=$2 VARIANT=baseline
make       PLATFORM=$1 CRYPTO_TARGET=NONE SS_VER=$2 VARIANT=baseline
# IRV 버전:
make clean PLATFORM=$1 CRYPTO_TARGET=NONE SS_VER=$2 VARIANT=irv
make       PLATFORM=$1 CRYPTO_TARGET=NONE SS_VER=$2 VARIANT=irv
```
- 핵심 차이: AES 예제는 `CRYPTO_TARGET=TINYAES128C`지만, **HAETAE는 자체 구현이라 `CRYPTO_TARGET=NONE`**.
- 출력 hex: `simpleserial-haetae-CW308_STM32F3.hex` (baseline/irv 각각 빌드 후 파일명을 바꿔 보관하세요).
- 두 버전을 구분하려면 빌드 후 `cp simpleserial-haetae-CW308_STM32F3.hex haetae-<variant>.hex`.

## ⚠️ RAM 주의 (STM32F303 = 40 KB)
HAETAE 포터블 레퍼런스는 스택 사용량이 커서 MODE2에서도 40 KB를 초과할 수 있습니다. 링크/실행 시
RAM 오버플로우가 나면:
- (권장) HAETAE **스택 축소 Cortex-M4 구현**으로 `haetae/`의 해당 소스를 교체, 또는
- RAM이 큰 타겟 사용: **CW308 + STM32F4**(`PLATFORM=CW308_STM32F4`, RAM 더 큼).
baseline/irv `sign.c`와 main은 두 경우 모두 그대로 적용됩니다.

## 트리거 동작
`trigger_high()/trigger_low()`는 CW의 `hal.h`(STM32F3 HAL)가 제공하며 GPIO4(TIO4) 트리거 핀을 토글합니다.
`-DCW_TARGET`로 컴파일하면 `sign_*.c`의 **민감 곱셈 `z = y + (-1)^b·c·s`(PolyMul 루프) 직전에
`trigger_high()`, 직후에 `trigger_low()`**가 삽입됩니다. 즉 스코프가 이 구간만 정확히 글리치하도록
`scope.glitch.trigger_src = "ext_single"`로 잡으면 됩니다. 별도 배선 불필요(CW308/CW-Lite 기본 트리거 핀).

## 호스트 커맨드 (simpleserial v1.1)
- `k` (0B): 키쌍 재생성(결정론적)
- `p` (1B): msg[0]=인자, DRBG 리셋 후 **서명**(트리거 발생), 응답 `r`=서명 앞 16바이트(상태)
- `c` (1B): 응답 `r`=서명의 `arg*64`바이트부터 64바이트 (반복 호출로 1474바이트 전체 수신)

## 실험 흐름
1. baseline hex 플래시 → `cw_glitch_campaign.py`로 글리치 스윕 → 공격 성공률 기록.
2. irv hex 플래시 → 동일 스윕 → 공격 성공률 기록.
3. 비교: 무방어 대비 IRV의 공격 성공률 감소, 그리고 사이클/시간/메모리 오버헤드.

호스트 스크립트 골격: `experiment_package/chipwhisperer/cw_glitch_campaign.py` (스코프/글리치 파라미터는
사용자 환경에 맞게 조정). 공격 성공 판정은 반환된 서명을 호스트에서 레퍼런스 검증(verify) 돌려
**검증 실패 + 골든과 상이**면 결함 서명으로 분류하세요.

## RNG에 대하여
`randombytes_drbg.c`는 고정 시드의 결정론적 DRBG입니다. **의도적**으로 모든 서명이 동일 nonce를 쓰게 하여
(같은 키·같은 y) baseline과 IRV를 1:1로 비교하고, skip 공격에서 골든 서명과 결함 서명을 정확히 대조할 수
있게 합니다. 실제 배포용이 아니며, 운영에서는 STM32 RNG 페리페럴로 교체해야 합니다.
