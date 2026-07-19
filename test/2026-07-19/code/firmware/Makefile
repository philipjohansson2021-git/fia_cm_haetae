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
# 축 A 인과 대조군(G3-4): 융합 대신 비융합 2-pass 로 +y 계산(무결함 시 산술 동일 → GOLDEN 보존).
#   make ... VARIANT=twopass FAULT_SIM=1   (loop-abort 로 물리 clean T2 실현 여부 확인)
ifeq ($(VARIANT),twopass)
  CDEFS += -DHAETAE_VARIANT_TWOPASS
endif

# 축 B: SW 라인별 결함주입 빌드 (대응기법 공정 비교). FAULT_SIM=1 로 활성.
#   make ... VARIANT=irv FAULT_SIM=1 MCU_CLK=INT   (결정론 주입은 INT 클럭으로 빠르게)
ifeq ($(FAULT_SIM),1)
  CDEFS += -DFAULT_SIM
endif

# 축 A fast-jig(G3-0) + 글리치 캘리브레이션(G3-1): 'J'/'C' 커맨드 추가, 스윕 8s→수십 ms.
#   make ... VARIANT=baseline AXISA_JIG=1   (또는 VARIANT=twopass AXISA_JIG=1)
#   FAULT_SIM 을 자동 포함하여 'x/s/c' 스트림·'T' 트리거·g_z1raw 덤프를 재사용한다.
ifeq ($(AXISA_JIG),1)
  CDEFS += -DAXISA_JIG -DFAULT_SIM
endif

# 축 A T1(c·s 스킵→z=y) 클린 실현용: c·s 스테이지 직전 cs1/cs2 사전 0화(스킵→z=y).
#   레퍼런스 기본 빌드는 미정의라 바이트동일. T1 인과대조 hex 에만 T1_CS_ZEROINIT=1 부여.
ifeq ($(T1_CS_ZEROINIT),1)
  CDEFS += -DT1_CS_ZEROINIT
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
