# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Public **reproduction repository** for a research paper on Fault Injection Attacks (FIA) against
**HAETAE** (KpqC lattice Fiat–Shamir-with-aborts signature) and a lightweight countermeasure,
**HAETAE-IRV** (Infective Randomized Verification). Author: Philip Johansson. Remote:
`github.com/philipjohansson2021-git/fia_cm_haetae`.

It holds **code, experiments, docs, and the compiled paper only — no LaTeX source** (the manuscript
is maintained elsewhere; only the built PDF lives in `paper/`). This is not a conventional software
product: there is no single app. The closest thing to a test suite is the x86 coverage simulation
(`test/2026-06-28/sim_code/common/`, `./test2` → 9/9 PASS).

Docs are Korean (`*_ko.md`). Reference implementation of HAETAE is bundled under
`docs/haetae_reference/` (official v1.1.2, MIT — see `docs/haetae_reference/SOURCE.md`).

## Repository layout

| Path | Contents |
|---|---|
| `README.md` | Project overview + headline results (Korean) |
| `docs/` | Algorithm docs (`HAETAE_overview_ko.md`, `HAETAE_signature_algorithm_ko.md`) + `haetae_reference/` (verbatim official HAETAE v1.1.2) |
| `firmware/simpleserial-haetae/` | ChipWhisperer STM32F4 full-signature FIA target (see below). Includes its own `haetae/` reference tree + `prebuilt/` |
| `test/YYYY-MM-DD/` | **Date-stamped experiment logs**, indexed by `test/README.md`. Each has `README.md` + `code/` + `results/` + `figures/` |
| `paper/` | Compiled paper PDF (`HAETAE_FIA_CM_IRV.pdf`) |
| `ppt/` | Presentation/explainer material (`.pptx`+`.pdf` decks, `explainer_ko.md`, `residual_computation_ko.md`, `slides_outline_ko.md`) |

## Cryptographic context (needed to read the code)

- Parameter set **HAETAE-120 / MODE2**: `Q=64513, LN=8192 (=2^13), N=256, L=4, M=L-1=3, K=2, η=1`.
  Ring `R_q = Z_q[x]/(x^256+1)`. Secret `s1` = 3 polynomials × 256 = **768 ternary {-1,0,1} coeffs**.
- Response (the only op using the secret): `z1[i] = y1[i] + (-1)^b · LN · (c·s1)[i]`.
- **Fault points (7):** own — **T1** (skip `c·s` → `z≈y`), **T2** (skip `+y` → `z=LN·c·s1`, leaks `s1`
  directly, single signature), **RB** (skip rejection → norm-over-B1 `z`); prior-work (Lee–Ha) —
  SEED/SIGNBIT/UNPACK/LSB.
- Key-recovery identity: `ŝ1[k] = NTT(z/LN)[k] · ĉ[k]⁻¹ mod q` (`c` is public). Bit-exact vs reference (768/768).
- Signing bound **B1 = 9838.98** (+ bimodal B0 = 9846.02) < verification bound **B2 = 12777.52** — the
  gap RB exploits and IRV's norm re-check (M5) closes.
- **Two experiment axes:** Axis **B** = SW line-injection (`FAULT_SIM`, the defender's upper bound —
  gives coverage/cost); Axis **A** = physical clock glitch (realizability — 07-05 T2 resists, 07-18 T1 recovers).

## Firmware (`firmware/simpleserial-haetae/`)

Full-signature FIA target for **CW308 + STM32F4** (needs 192 KB RAM; F3 overflows), built as a
*whole project folder* (`CRYPTO_TARGET=NONE` — HAETAE is self-contained, not TinyAES).

Key design: **one signing function + VARIANT macros** in `haetae_sign_cm.c`; `main` in
`simpleserial-haetae.c` (commands `k`/`p`/`z`/`t`; `T`/`f`/`x`/`s`/`c` under FAULT_SIM; `J` under AXISA_JIG).
`keypair`/`verify`/reference arithmetic come from the bundled `haetae/` tree; RNG is a **fixed-seed
deterministic DRBG** (`haetae/randombytes_drbg.c`) *on purpose* — identical nonce lets baseline/IRV and
golden/faulty be compared 1:1 (not for deployment).

Build-time countermeasure `VARIANT` (all macro-guarded → a flagless build is byte-identical to the reference):
- `baseline` — undefended
- `irv` (`-DHAETAE_VARIANT_IRV`) — **HAETAE-IRV**: integrity checks (`c·s` recompute, B1+B0 norm re-check,
  seed sanity, (y,b) re-derive, sk checksum; standard-verify runs in `main`) accumulate into a residual
  `cm_delta`, then **branchless infective masking** `sig ^= SHAKE(seed‖δ‖μ) & factor` (factor = 0x00 if
  δ=0 else 0xFF). No detect-and-abort branch → resists second-order branch-skip faults. The paper's core.
- `double` (`-DHAETAE_VARIANT_DOUBLE`) — dual computation + compare in `main` (~2× time)
- `leeha` (`-DHAETAE_VARIANT_LEEHA`) — reimplements Lee–Ha (JKIISC 2026); sign-then-verify is in `main`
- `twopass` (`-DHAETAE_VARIANT_TWOPASS`) — non-fused 2-pass `+y`, the Axis-A causal control

Experiment flags: `FAULT_SIM=1` (Axis-B SW injection: `f`/`x`/`s`/`c`/`T` commands), `AXISA_JIG=1`
(fast-jig `J`, auto-enables FAULT_SIM), `T1_CS_ZEROINIT=1` (pre-zero `cs` — the disclosed T1 causal control).

### Building the firmware
The `makefile` `include`s the ChipWhisperer framework (`../simpleserial/Makefile.simpleserial`,
`../Makefile.inc`), which is **not in this repo**. To build, drop `simpleserial-haetae/` into a
ChipWhisperer checkout at `firmware/mcu/` and build in **WSL** (`arm-none-eabi-gcc`):
```bash
B='PLATFORM=CW308_STM32F4 CRYPTO_TARGET=NONE SS_VER=SS_VER_1_1'
make clean $B VARIANT=irv && make $B VARIANT=irv       # add FAULT_SIM=1 / AXISA_JIG=1 / T1_CS_ZEROINIT=1 as needed
```
- One-time: F4 HAL is a ChipWhisperer submodule (`git submodule update --init firmware/mcu/hal/chipwhisperer-fw-extra`).
- **F4 clock:** internal 168 MHz (`MCU_CLK=INT`) is broken (flash wait-state bug) — use the default
  HSE-direct build (external 7.37 MHz; `scope.clock.clkgen_freq=7.37e6`, `scope.io.hs2='clkgen'`; PLL bypassed so glitching works).
- **`.hex` is gitignored** (build artifact) — build from source; `prebuilt/` hexes are not tracked.
- The trigger wraps the sensitive multiply; scope with `glitch.trigger_src="ext_single"`.

## Runnable: x86 coverage/overhead simulation (the "test suite")

Self-contained (bundles its own `haetae_src/`), architecture-independent. In `test/2026-06-28/sim_code/common/`:
```bash
make            # builds campaign, overhead, test2
./test2         # invariant unit checks — expect 9/9 PASS (closest thing to a test suite)
./campaign      # 12 fault-points × 6 fault-models × countermeasures → CSV
./overhead      # relative overhead of each countermeasure (x86)
```
`sign_fi.c` = instrumented HAETAE signer with fault hooks + baseline/IRV/Lee-Ha logic (CM mode);
`by_countermeasure/{baseline,double,leeha,irv}.c` are per-CM excerpts.

## Host tooling & recovery

Host scripts run in a conda env **`aifia`** (Python 3.11, chipwhisperer 6.0.0) — launched via
`run_aifia.bat` (in the `test/*/code/` dirs; Jupyter port 8899, kernel "Python (aifia)"). For Korean
stdout set `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` (else cp949 errors).

- **Recovery (Python, bit-exact vs reference):** `test/*/code/haetae_recover.py` (T2/single-signature
  core: NTT + `ŝ1=NTT(z/LN)·ĉ⁻¹`) and `haetae_recover_t1.py` (T1 2-signature-output differential
  `z_clean−z_fault` + `verify_s1`). *Note the code identifiers `recover_s1_from_two_traces`/`verify_two_traces`
  are the C/Python function names — do not "translate" them.*
- **Public-key verification (C):** `test/2026-07-19/code/verify_s1_pubkey.c` confirms a recovered `s1`
  using **only the public key** (no true-key oracle) — build in WSL linking `docs/haetae_reference/`
  (`build_verify_s1_pubkey.sh`). self-test: true s1 → PASS, any wrong s1 → FAIL.
- **Hardware gotcha:** the ChipWhisperer-Husky takes exclusive USB — a live Jupyter kernel holding
  `scope` blocks standalone scripts. Release with `scope.dis()` or kill the kernel; autonomous drivers
  (e.g. `test/2026-07-18/code/t1_auto.py`) call `scope.dis()` on completion.

## Experiment logs (`test/YYYY-MM-DD/`, indexed by `test/README.md`)

Chronology (read `test/README.md` for the authoritative index + headline numbers):
- **2026-06-28** — x86 coverage/overhead sim (IRV vs Lee-Ha vs double).
- **2026-06-30** — STM32F4 full-sign Axis-B SW injection: coverage **irv 7/7 · double 7/7 · leeha 6/7 (RB
  miss)**; 2nd-order (check-branch skip) → **only IRV blocks**; cost **irv/leeha 1.14× · double 2.0×**;
  T2 single-signature s1 100%.
- **2026-07-01 / 07-05** — Axis-A bring-up + T2 physical: the fused `+y` reference **resists** clean
  single-glitch T2 (N=300: LEAK 0).
- **2026-07-18** — Axis-A **T1**: real clock-glitch multi-fault accumulation recovers **s1 768/768** (2
  faulty signatures).
- **2026-07-19** — public-key recovery verification (W2) + full-sign cross-check driver (W3) + T1 reproduction.

**New results go under `test/<today>/` and get one row in `test/README.md`.**

## Honesty conditions (must be preserved in code, docs, and paper)

For the physical (Axis-A) attack claims: (a) the **causal-control build** is disclosed
(`T1_CS_ZEROINIT` pre-zeros `cs`; the **unmodified fused reference resists** — a skip yields garbage,
not a clean `z=y`); (b) **fixed nonce** (deterministic DRBG / jig replay) is required by the 2-signature
differential; (c) success is judged by **exact coefficient-wise match against the device's true `s1`**
(the `s` stream), and can also be confirmed public-key-only via `verify_s1_pubkey`. Frame physical T1 as
a *realizability study + IRV motivation*, never as "broke the reference."

## Conventions

- **Terminology:** docs use **"서명 출력(값)"** = a signature output; **N-서명 출력 차분** = an N-signature
  differential. This is NOT the SCA power/EM "trace" — this is a fault-injection attack, not side-channel.
- **`paper/` holds only the compiled PDF**; the LaTeX manuscript is edited outside this repo.
- Git pushes are done by the user.
