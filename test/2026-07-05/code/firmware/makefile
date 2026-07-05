# ChipWhisperer firmware makefile — HAETAE 전체 서명 결함주입 타겟 (STM32F4).
# 4개 변형을 VARIANT 로 선택해 각각 빌드:
#   make clean PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline
#   make       PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1 VARIANT=baseline
#   (VARIANT = baseline | double | leeha | irv)
# 출력: simpleserial-haetae-CW308_STM32F4.hex  → 변형별로 파일명을 바꿔 보관 권장.
# ※ F4 빌드 전 1회: chipwhisperer-fw-extra 서브모듈 init (hal/stm32f4 제공)
#     git submodule update --init firmware/mcu/hal/chipwhisperer-fw-extra

TARGET = simpleserial-haetae

VARIANT ?= baseline     # baseline | double | leeha | irv

ifeq ($(VARIANT),irv)
  CDEFS += -DHAETAE_VARIANT_IRV
endif
ifeq ($(VARIANT),leeha)
  CDEFS += -DHAETAE_VARIANT_LEEHA
endif
ifeq ($(VARIANT),double)
  CDEFS += -DHAETAE_VARIANT_DOUBLE
endif

# 축 B: SW 라인별 결함주입 빌드 (대응기법 공정 비교). FAULT_SIM=1 로 활성.
#   make ... VARIANT=irv FAULT_SIM=1 MCU_CLK=INT   (결정론 주입은 INT 클럭으로 빠르게)
ifeq ($(FAULT_SIM),1)
  CDEFS += -DFAULT_SIM
endif

# 타겟 main + 단일 대응기법 서명(haetae_sign_cm.c, VARIANT 매크로로 분기)
SRC += simpleserial-haetae.c haetae_sign_cm.c
# 레퍼런스 keypair/verify 제공원 (서명 internal 은 haetae_sign_cm 이 대체; 미사용 함수는 GC)
SRC += sign_baseline.c
# HAETAE 레퍼런스 소스 + 결정론 DRBG
SRC += decompose.c encoding.c fft.c fixpoint.c ntt.c packing.c poly.c \
       polyvec.c polymat.c polyfix.c reduce.c sampler.c fips202.c \
       symmetric-shake.c randombytes_drbg.c

# HAETAE 소스/헤더 위치 (flat object names via VPATH)
VPATH += haetae
EXTRAINCDIRS += haetae/include

# CW 트리거 훅 + HAETAE-120 (mode2)
CDEFS += -DCW_TARGET -DHAETAE_CONFIG_MODE=HAETAE_MODE2

#Add simpleserial project to build
include ../simpleserial/Makefile.simpleserial

FIRMWAREPATH = ../.
include $(FIRMWAREPATH)/Makefile.inc
