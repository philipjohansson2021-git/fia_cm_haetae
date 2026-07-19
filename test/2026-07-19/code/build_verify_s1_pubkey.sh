#!/usr/bin/env bash
# Build the public-only s1 verifier (verify_s1_pubkey) in WSL.
# Links the full HAETAE reference + the device's fixed-seed DRBG, so the host
# reproduces the exact device public key. Run from anywhere.
#   wsl.exe bash -s < build_verify_s1_pubkey.sh      # (CRLF-safe via stdin)
# If run as a file and you see "\r" errors: sed -i 's/\r$//' build_verify_s1_pubkey.sh
set -e
REF=/mnt/d/06_github_desktop/fia_cm_haetae/docs/haetae_reference
DRBG=/mnt/d/06_github_desktop/fia_cm_haetae/firmware/simpleserial-haetae/haetae/randombytes_drbg.c
HERE=/mnt/c/Users/NSRSGW/ChipWhisperer/chipwhisperer/jupyter/courses/fault_haetae_cm
SRCS=$(ls "$REF"/src/*.c | grep -v '/randombytes.c')   # DRBG replaces reference randombytes
gcc -O2 -I"$REF/include" -DHAETAE_CONFIG_MODE=HAETAE_MODE2 \
    $SRCS "$DRBG" "$HERE/verify_s1_pubkey.c" \
    -o "$HERE/verify_s1_pubkey"
echo "built: $HERE/verify_s1_pubkey"
"$HERE/verify_s1_pubkey"   # self-test
