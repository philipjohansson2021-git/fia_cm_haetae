// SPDX-License-Identifier: MIT
// verify_s1_pubkey.c — PUBLIC-ONLY validation of a recovered HAETAE s1.
//
// Purpose (closes the "true-key oracle" gap, review item W2):
//   Confirm that a recovered secret s1 is correct using ONLY the public key
//   (seed_A, b) — never comparing against the device's true s1. An attacker in
//   the field has exactly this: the public key + the recovered s1.
//
// Math (HAETAE MODE2 keygen, D=1 rounding):
//   b_full = a + A0*s1 + s2  (mod q),   b1 = HighBits(b_full) = (b_full-b0)/2,
//   b0 in {-1,0,1}, and the public key stores (seed_A, b1).
//   For a candidate s1, let  w = a + A0*s1_cand  (reference arithmetic). Then
//     center_q(2*b1 - w) = s2 - b0    (both small, |.| <= ~3)  iff s1_cand = s1.
//   A wrong s1 makes w ~uniform mod q, so 2*b1 - w is ~uniform -> essentially
//   no coefficient is small. This is a crisp, fully public discriminator.
//
// The device key is deterministic (fixed-seed SHAKE DRBG), so the host
// reproduces the exact public key with randombytes_reset()+crypto_sign_keypair.
// The secret key is unpacked ONLY to run the self-test (true s1 must PASS,
// any wrong s1 must FAIL); the verification predicate itself uses pk alone.
//
// Build (WSL): see companion build command. Run:
//   ./verify_s1_pubkey                 # self-test (proves the check is sound)
//   ./verify_s1_pubkey recovered.txt   # check a recovered s1 (768 ints, coeff
//                                       # domain {-1,0,1}, row-major m*256+k)

#include "api.h"
#include "params.h"
#include "packing.h"
#include "poly.h"
#include "polyvec.h"
#include "polymat.h"
#include "randombytes.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

void randombytes_reset(void);

static int32_t center_q(int32_t x) {
  x %= HAETAE_Q;
  if (x < 0) x += HAETAE_Q;
  if (x > HAETAE_Q / 2) x -= HAETAE_Q;
  return x;
}

// w = a + A0 * s1cand  (normal domain, frozen to [0,q)) — matches keygen's b-path.
static void compute_w(polyveck *w, const polyvecm *s1cand,
                      const polyvecm A[HAETAE_K], const polyveck *a) {
  polyvecm s1hat = *s1cand;
  polyvecm_ntt(&s1hat);
  polymatkm_pointwise_montgomery(w, A, &s1hat);
  polyveck_invntt_tomont(w);
  polyveck_add(w, w, a);
  polyveck_freeze(w);
}

// worst |center_q(2*b1 - w)| over K*N coeffs; *nbad = #coeffs with |.|>T.
static int32_t check(const polyvecm *s1cand, const polyvecm A[HAETAE_K],
                     const polyveck *a, const polyveck *b1, int T, int *nbad) {
  polyveck w;
  compute_w(&w, s1cand, A, a);
  int32_t worst = 0;
  *nbad = 0;
  for (unsigned int i = 0; i < HAETAE_K; i++)
    for (int k = 0; k < HAETAE_N; k++) {
      int32_t d = center_q(2 * b1->vec[i].coeffs[k] - w.vec[i].coeffs[k]);
      int32_t ad = d < 0 ? -d : d;
      if (ad > worst) worst = ad;
      if (ad > T) (*nbad)++;
    }
  return worst;
}

static void negate_s1(polyvecm *d, const polyvecm *s) {
  for (unsigned int i = 0; i < HAETAE_M; i++)
    for (int k = 0; k < HAETAE_N; k++)
      d->vec[i].coeffs[k] = -s->vec[i].coeffs[k];
}

int main(int argc, char **argv) {
  uint8_t pk[CRYPTO_PUBLICKEYBYTES], sk[CRYPTO_SECRETKEYBYTES];
  randombytes_reset();
  crypto_sign_keypair(pk, sk); // reproduces the DEVICE key (fixed-seed DRBG)

  // ---- PUBLIC inputs only: seed_A (=pk[0:32]) and b1 (from pk) ----
  polyvecm A[HAETAE_K];
  polyveck a, b1;
  polymatkm_expand_matA(A, pk);
  polyveck_expand_vecA(&a, pk);
  for (unsigned int i = 0; i < HAETAE_K; i++)
    unpack_poly_q(&b1.vec[i], pk + HAETAE_SEEDBYTES + i * HAETAE_POLYQ_PACKEDBYTES);

  // ---- true s1 (from sk) — used ONLY for the self-test / demonstration ----
  polyvecl Adummy[HAETAE_K];
  polyvecm s1true;
  polyveck s2true;
  uint8_t key[HAETAE_SEEDBYTES];
  unpack_sk(Adummy, &s1true, &s2true, key, sk);

  const int T = 8; // slack; correct key yields |.| <= ~3
  int nbad;
  int32_t worst;
  const int NC = HAETAE_K * HAETAE_N;

  printf("== HAETAE public-only s1 verification (review item W2) ==\n");
  printf("predicate uses ONLY pk (seed_A, b); secret shown for self-test only.\n");
  printf("q=%d  K*N=%d  slack T=%d\n\n", HAETAE_Q, NC, T);

  worst = check(&s1true, A, &a, &b1, T, &nbad);
  printf("[true s1      ] worst|2b1-w|=%6d  bad(>%d)=%d/%d  -> %s\n", worst, T,
         nbad, NC, nbad == 0 ? "PASS" : "FAIL");

  polyvecm s1neg;
  negate_s1(&s1neg, &s1true);
  worst = check(&s1neg, A, &a, &b1, T, &nbad);
  printf("[-s1 (wrong b)] worst|2b1-w|=%6d  bad(>%d)=%d/%d  -> %s\n", worst, T,
         nbad, NC, nbad == 0 ? "PASS" : "FAIL");

  polyvecm s1bad = s1true;
  s1bad.vec[0].coeffs[0] += 1; // flip a single coefficient
  worst = check(&s1bad, A, &a, &b1, T, &nbad);
  printf("[1-coeff wrong] worst|2b1-w|=%6d  bad(>%d)=%d/%d  -> %s\n", worst, T,
         nbad, NC, nbad == 0 ? "PASS" : "FAIL");

  if (argc > 1) {
    FILE *f = fopen(argv[1], "r");
    if (!f) { perror("open"); return 1; }
    polyvecm rec;
    for (unsigned int i = 0; i < HAETAE_M; i++)
      for (int k = 0; k < HAETAE_N; k++) {
        long v;
        if (fscanf(f, "%ld", &v) != 1) { fprintf(stderr, "need 768 ints\n"); return 1; }
        rec.vec[i].coeffs[k] = (int32_t)v;
      }
    fclose(f);
    int nb1, nb2;
    int32_t w1 = check(&rec, A, &a, &b1, T, &nb1);
    polyvecm recn;
    negate_s1(&recn, &rec);
    int32_t w2 = check(&recn, A, &a, &b1, T, &nb2);
    int ok = (nb1 == 0) || (nb2 == 0);
    printf("\n[recovered s1 ] +sign: worst=%d bad=%d ; -sign: worst=%d bad=%d\n",
           w1, nb1, w2, nb2);
    printf("  -> %s  (resolved sign: %s)\n",
           ok ? "PASS — recovered s1 is consistent with the PUBLIC key" : "FAIL",
           nb1 == 0 ? "+" : (nb2 == 0 ? "-" : "?"));
  }
  return 0;
}
