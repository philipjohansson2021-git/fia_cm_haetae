// SPDX-License-Identifier: MIT
// Deterministic SHAKE-based DRBG replacing the OS randombytes() for the
// ChipWhisperer target. Determinism is intentional: it makes every signature
// reproducible, so a glitched (faulted) signature can be compared 1:1 against
// the golden one, and baseline vs IRV use the SAME nonce. NOT for production.
#include "randombytes.h"
#include "fips202.h"
#include <stdint.h>
#include <string.h>

static uint8_t  drbg_seed[32] = {
  0xA5,0x5A,0x00,0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,0x99,0xAA,0xBB,0xCC,0xDD,
  0xEE,0xFF,0x01,0x23,0x45,0x67,0x89,0xAB,0xCD,0xEF,0x10,0x32,0x54,0x76,0x98,0xBA};
static uint64_t drbg_ctr = 0;

void randombytes_reset(void){ drbg_ctr = 0; }            // call before each sign
void randombytes_seed(const uint8_t s[32]){ memcpy(drbg_seed,s,32); drbg_ctr=0; }

int randombytes(uint8_t *out, size_t outlen){
  uint8_t in[40];
  memcpy(in, drbg_seed, 32);
  while(outlen){
    for(int i=0;i<8;i++) in[32+i]=(uint8_t)(drbg_ctr>>(8*i));
    drbg_ctr++;
    uint8_t blk[168];                          // SHAKE256 rate
    size_t n = outlen<168?outlen:168;
    shake256(blk, n, in, 40);
    memcpy(out, blk, n);
    out+=n; outlen-=n;
  }
  return 0;
}
