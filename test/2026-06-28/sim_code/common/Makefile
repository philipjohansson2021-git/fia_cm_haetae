# 자체완결 x86 빌드 (레퍼런스 소스 동봉: haetae_src/, include/).
MODE=HAETAE_MODE2
CFLAGS=-O2 -Iinclude -DHAETAE_CONFIG_MODE=$(MODE)
# 결함 internal은 sign_fi.c, keypair/verify는 haetae_src/sign.c, RNG는 결정론 fi_rng.c
REFSRCS=$(filter-out haetae_src/randombytes.c, $(wildcard haetae_src/*.c))
COMMON=sign_fi.c fi_rng.c $(REFSRCS)

all: campaign overhead test2
campaign: campaign.c $(COMMON) ; gcc $(CFLAGS) $^ -o $@
overhead: overhead.c $(COMMON) ; gcc $(CFLAGS) $^ -o $@
test2:    test2.c    $(COMMON) ; gcc $(CFLAGS) $^ -o $@
clean: ; rm -f campaign overhead test2
