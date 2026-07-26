---
marp: true
theme: default
size: "16:9"
lang: ko
math: mathjax
paginate: true
header: "HAETAE Fault Injection Attacks and Countermeasures"
footer: ""
title: "양자 내성 암호 HAETAE에 대한 오류 주입 공격 및 대응 기법"
author: "Sangwon Lee · Yunsung Kim · Jaecheol Ha"
---

<style>
section {
    background: #fdfdff;
    color: #1f2937;
    font-size: 28px;
    line-height: 1.45;
    padding: 60px 80px;
    word-break: keep-all;
    overflow-wrap: break-word;
}

section h1,
section h2 {
    text-align: center;
}

section h1 {
    font-size: 1.8em;
}

section h2 {
    font-size: 1.35em;
}

section pre {
    font-size: 21px;
    line-height: 1.35;
}

section table {
    display: table;
    margin: 0.5em auto;
    max-width: 100%;
    font-size: 0.9em;
}

section img {
    display: block;
    margin: 0 auto;
}

section blockquote {
    margin: 0.7em 0;
    padding-left: 1em;
    border-left: 4px solid #6b7280;
}

header {
    font-size: 16px;
}

section::after {
    content: attr(data-marpit-pagination) " / " attr(data-marpit-pagination-total);
    font-size: 11px;
}

section.lead {
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
}

section.divider h1 {
    padding-bottom: 0.15em;
    border-bottom: 2px solid #374151;
}

section.small {
    font-size: 22px;
}

section.code-small pre {
    font-size: 18px;
}

section.tiny {
    font-size: 18px;
}

section.code-tiny pre {
    font-size: 14px;
}

.columns {
    display: flex;
    gap: 48px;
    align-items: flex-start;
}

.column {
    flex: 1;
    min-width: 0;
}

.takeaway {
    margin: 0.7em 0;
    padding: 0.55em 1em;
    border: 1px solid #9ca3af;
    border-left: 6px solid #1f3a8a;
    background: #f5f7ff;
    font-weight: 700;
    text-align: center;
}

.references {
    font-size: 0.78em;
    line-height: 1.45;
}

.contact {
    font-size: 0.85em;
    text-align: center;
}

section.lead header,
section.lead footer,
section.lead::after {
    display: none;
}
</style>

<!-- source: P-001 | §0 | p.429 -->
<!-- _class: lead -->
# 양자 내성 암호 HAETAE에 대한 </br> 오류 주입 공격 및 대응 기법

### Fault Injection Attacks on Post-Quantum Cryptography Algorithm 
### HAETAE and Their Countermeasures

**Sangwon Lee† · Yunsung Kim · Jaecheol Ha‡** 
Hoseo University (Graduated Student, Professor)

Journal of The Korea Institute of Information Security & Cryptology 
VOL.36, NO.2, Apr. 2026 · p.429 
DOI: [10.13089/JKIISC.2026.36.2.429](https://doi.org/10.13089/JKIISC.2026.36.2.429)

---

## 목차

1. 들어가기에 앞서 — *Dilithium* FI 배경 [9]–[12]
2. 요약
3. I. 서론
4. II. 관련 연구 및 배경 지식
5. III. *HAETAE* 서명 알고리즘 오류 주입 공격
6. IV. 실험 설계 및 구현
7. V. 대응 기법
8. VI. 결론

---

<!-- _class: lead divider -->
# 들어가기에 앞서 </br> Dilithium FI 배경 [9]–[12]

*참고문헌 [9]–[12] · 출판 연도순 · FIPS 204 대조*

---

<!-- source: preface | HAETAE §I -->
## 왜 [9]–[12]를 먼저 보는가

**출처:** 대상 논문 §I (p.430)

*Dilithium* 에는 다양한 *fault injection* 공격이 보고되어, 단일 또는 다중 오류로 비밀키 복구가 실험적으로 입증되었다 ([9]–[12]).  
반면 *HAETAE* 에 대한 FI 연구는 매우 제한적이며, 전체 서명 과정에 대한 종합 분석은 아직 보고되지 않았다.

본 절에서는 대상 논문이 인용하는 [9]–[12]의 공격 지점과 키 복구 논리를 정리하고, 필요한 경우 FIPS 204 (*ML-DSA*) 의사코드와 대조한다.  
(*Fault injection* 의 성패는 구현에 좌우될 수 있다.)

---

<!-- source: P-009 + REF-[9–12] -->
<!-- _class: tiny -->
## Dilithium FI [9]–[12] — 한눈에 보기

**출처:** 대상 논문 §I 참고문헌 [9]–[12].

| 문헌 | 출판 | 오류 주입 대상(시점·연산) | 오류 데이터 → 비밀키 로직 | 비고 |
|------|------|---------------------------|---------------------------|------|
| [11] | TCHES 2023 No.2 | **NTT twiddle** zeroization (**1 fault**, *EMFI*) | 엔트로피 붕괴 → *Dilithium* 위조·검증 우회 | pqm4 M4 |
| [9] | TCHES 2023 No.4 | **y**-sampling: *ExpandMask* **nonce++ skip** → $y[i]=y[j]$ | $\Delta z=c(s_1[i]-s_1[j])$ → *MLWE*→**RLWE** → lattice | *DFA*, det+rand |
| [10] | TCHES 2024 No.3 | **(1)** $z=y+cs_1$ **덧셈 skip** · **(2)** **ExpandA** 한 계수 fault | **Correction**: verify 통과 중간값 열거 → $s_1$ | rand/hedged + glitch |
| [12] | FDTC 2024 | **hedged $\rho'$** *SHAKE* **absorb skip** (voltage) | 예측 $y$ → $\mathbf{s}_1=(\mathbf{z}-\mathbf{y})c^{-1}$ · **1 sig** ~53% | CW-Husky·STM32 |


---

<!-- source: REF framework legend | audience-facing -->
<!-- _class: tiny -->
## 참고문헌 정리 항목

각 문헌([9]–[12])을 아래 항목으로 정리한다.

| 항목 | 뜻 |
|------|-----|
| **주입 대상** | *fault* 를 넣는 연산·시점 |
| **키 복구** | 오류 출력에서 비밀키를 얻는 논리 |
| **서명 모드** | *deterministic* / *randomized* (·*hedged*) |
| **오류 횟수** | 필요한 *fault*·오류 서명 수 |
| **공격 실증** | 소프트웨어 시뮬레이션 · 하드웨어 *fault* 실증 |
| **HAETAE 연계** | 대상 논문 구조와의 대응 |
| **한계** | 전제·대응·과장 주의점 |

---

<!-- source: REF-11 -->
## [11] 개요

**출처:** [11] Abstract (TCHES 2023)

> *“we present the first fault injection analysis of the Number Theoretic Transform (NTT). … zeroization of the twiddle constants significantly reduces the entropy of its output.”*

| 항목 | 논문 주장 |
|------|-----------|
| 커널 | *NTT* (*Kyber* · *Dilithium*) |
| 핵심 | *twiddle constants zeroization* → *entropy collapse* |
| 실험 | *EMFI*, ARM Cortex-M4, **pqm4** |
| *Dilithium* | *existential forgery* + *verification bypass* |

---

<!-- source: [11] roadmap | audience -->
<!-- _class: tiny -->
## [11] 읽기 순서

이 문헌은 다음 순서로 본다.

| 단계 | 내용 |
|------|------|
| 1 | *NTT* 와 *twiddle* 오류 모델 (FIPS Algorithm 41) |
| 2 | 출력이 한 계수로 붕괴하는 이유 (수치 예) |
| 3 | *Sign* 경로에서 그 오류가 키 복구로 이어지는 방식 (Attack-1·2) |
| 4 | *Verify* 우회 (Verification-Bypass) |
| 5 | 구현 의존·한계 |

공통 전제: *fault* 성공 여부는 **구현**에 좌우될 수 있다.

---

<!-- source: REF-11 A -->
## [11] 주입 대상 — *NTT twiddle*

**출처:** [11] §4 + *pqm4* *NTT* 어셈블리 관찰 (ARM Cortex-M4)

1. *Twiddle constants* 는 flash 상수 배열; **twiddle-pointer** 로 일괄 참조
2. 단일 *EMFI* 로 pointer 를 0-영역으로 → **전 *twiddle* zeroization** (논문 실험)
3. 대수: *Cooley–Tukey butterfly* 에서 $w=0$ → 입력 한 계수 반복 (*entropy collapse*)

| 층위 | 내용 |
|------|------|
| **구현** | *pqm4* · *EMFI* · M4 |
| **대수** | FIPS 204 Alg 41, $z\leftarrow\texttt{zetas}[m]$ |

---

<!-- source: REF-11 B -->
## [11] 공격 결과 한눈에

**출처:** [11] §6.

*NTT* 출력이 저엔트로피로 바뀌면, 이후 다항식 곱·서명이 공격에 유리하게 변한다 (논문).

| 절차 | 논문이 보인 결과 |
|------|------------------|
| *Sign* | *deterministic* / *probabilistic* 에서 키 관련 정보 유출 → *existential forgery* 경로 |
| *Verify* | 잘못된 서명 수락 강제 (*verification bypass*) |
| (참고) *Kyber* | 동일 *NTT* 취약점으로 키·메시지 복구 |

수식·의사코드는 바로 이어지는 Algorithm 41 과 Attack-1·2 에서 전개한다.

---

<!-- source: REF-11 C–G -->
## [11] 서명모드·횟수·한계

| 항목 | 내용 |
|------|------|
| **서명 모드** | 단일 *EM fault*; 서명·검증 절차 |
| **오류 횟수** | **1 fault** 중심; *EMFI* 고성공률 |
| **공격 실증** | **EMFI 실측** (글리치 논문과 수단 상이) |
| **HAETAE 연계** | *HAETAE* **NTT** 사용 시 공통 공격면 후보 (구현 동일 여부는 별도 확인) |
| **한계** | *NTT* 전용 대응 필요; 기존 *Verify_After_Sign* 등만으로 부족 가능 |

---

<!-- source: DIL-11-U1 | FIPS 204 Alg 41 | unmodified -->
<!-- _class: code-tiny -->
## FIPS 204 — Algorithm 41 $\mathrm{NTT}(w)$ (1/2)

> 출처: NIST FIPS 204, §7.5 Algorithm 41.

**Algorithm 41** $\mathrm{NTT}(w)$ 
Computes the *NTT*.

**Input:** Polynomial $w(X)=\sum_{j=0}^{255} w_j X^j \in R_q$. 
**Output:** $\hat{w}=(\hat{w}[0],\ldots,\hat{w}[255])\in T_q$.

```
 1: for j from 0 to 255 do
 2:     ŵ[j] ← w_j
 3: end for
 4: m ← 0
 5: len ← 128
 6: while len ≥ 1 do
 7:     start ← 0
 8:     while start < 256 do
 9:          m ← m + 1
10:          z ← zetas[m]       ▷ z ← ζ^{BitRev8(m)} mod q
11:          for j from start to start + len − 1 do
12:              t ← (z · ŵ[j + len]) mod q
13:              ŵ[j + len] ← (ŵ[j] − t) mod q
14:              ŵ[j] ← (ŵ[j] + t) mod q
15:          end for
```

---

<!-- source: DIL-11-U1 | FIPS 204 Alg 41 | unmodified -->
<!-- _class: code-tiny -->
## FIPS 204 — Algorithm 41 $\mathrm{NTT}(w)$ (2/2)

```
16:          start ← start + 2 · len
17:     end while
18:     len ← ⌊len/2⌋
19: end while
20: return ŵ
```

* 사전계산: $\texttt{zetas}[1..255]$ (FIPS 204 Appendix B; $\zeta=1753\in\mathbb{Z}_q$)
* Line 10–14: *Cooley–Tukey butterfly* with *twiddle* $z$
* $\mathrm{len}=128,64,\ldots,1$ → **complete** *NTT* (8 *stages*, $n=256$)

---

<!-- source: DIL-11-U1 | 역할 -->
## Algorithm 41이 하는 일

**출처:** NIST FIPS 204, Algorithm 41.

* *Number Theoretic Transform* (*NTT*): $R_q$ 다항식을 $T_q$ 표현으로 변환
* 다항식 곱을 *NTT domain*의 *pointwise multiplication* ($\circ$) + $\mathrm{NTT}^{-1}$ 로 계산

$$
a\cdot b \;=\; \mathrm{NTT}^{-1}\big(\mathrm{NTT}(a)\,\circ\,\mathrm{NTT}(b)\big)
$$

* ML-DSA *Sign* / *Verify* / *KeyGen* 이 공통으로 호출하는 커널
* 오류 모델이 겨냥하는 줄: **L10** $z\leftarrow\texttt{zetas}[m]$

---

<!-- source: DIL-11-U1 | z=0 -->
## $z=0$ 일 때 (대수 · 표준만으로 검증)

**출처:** FIPS 204 Algorithm 41 **L10–14** 에 $z=0$ 대입.

L12에서 $t\leftarrow(z\cdot\hat{w}[j+\mathrm{len}])\bmod q$. 
**모든** *twiddle* $z=0$ 이면 $t=0$:

$$
\hat{w}[j+\mathrm{len}]\leftarrow\hat{w}[j],\qquad
\hat{w}[j]\leftarrow\hat{w}[j]
$$
<div class="takeaway">전 *stage* 적용 시 출력 $\hat{w}[i]=w_0$ ($\forall i$)</div>

<div class="takeaway">*entropy collapse* (입력 첫 계수 반복)</div>


| 층위 | 내용 | 성격 |
|------|------|------|
| **대수** | $z=0$ → 위 붕괴 | FIPS Alg 41로 **검증 가능** |
| **구현** | *twiddle-pointer* 1회 *EMFI* 로 전 $z=0$ | **구현·보드 의존** ([11] pqm4 M4) |

---

<!-- source: DIL-11-U1 | z=0 numeric example -->
<!-- _class: tiny -->
## $z=0$ 수치 예제 (ML-DSA 모듈러스)

**출처:** FIPS 204 — $q=8380417$, Alg 41 L12–14.

한 *butterfly* ($j=0$, $\mathrm{len}=128$). 배열에 들어 있는 값:

$$
\hat{w}[0]=42,\qquad \hat{w}[128]=1000,\qquad q=8380417
$$

| | $z$ (twiddle) | $t=(z\cdot\hat{w}[128])\bmod q$ | 갱신 후 $\hat{w}[128]$ | 갱신 후 $\hat{w}[0]$ |
|--|---------------|----------------------------------|------------------------|----------------------|
| 정상 예 | $1753$ | $(1753\cdot 1000)\bmod q=1753000$ | $(42-1753000)\bmod q=6627459$ | $(42+1753000)\bmod q=1753042$ |
| **오류** | **$0$** | $(0\cdot 1000)\bmod q=\mathbf{0}$ | $(42-0)\bmod q=\mathbf{42}$ | $(42+0)\bmod q=\mathbf{42}$ |

$z=0$ 이면 **한 번의 butterfly** 는 “$\hat{w}[j+\mathrm{len}]\leftarrow\hat{w}[j]$” 복사일 뿐이다.  
한 *butterfly* 만으로는 $\hat{w}[1]$ 이 바뀌지 않는다. 여러 *stage* 를 거치면 $w_0$ 으로 맞춰진다.

---

<!-- source: DIL-11-U1 | z=0 multi-stage why w[1] -->
<!-- _class: tiny -->
## 왜 $\hat{w}[1]$ 도 같은 값이 되나 (Alg 41 구조)

**출처:** FIPS 204 Algorithm 41 — $\mathrm{len}=128,64,\ldots,1$ (**8 stage**). 아래는 $n=8$ 축소 예.

$z=0$ 이면 매 butterfly 는 항상

$$
\hat{w}[j+\mathrm{len}] \leftarrow \hat{w}[j]
$$

즉 **왼쪽 인덱스의 값이 오른쪽 인덱스로 복사**된다. $\hat{w}[0]$ 은 왼쪽 끝이라 끝까지 $w_0$ 으로 남는다.

| stage ($\mathrm{len}$) | $z=0$ 일 때 하는 일 (요지) | $\hat{w}[1]$ |
|------------------------|------------------------------|--------------|
| $4$ (큰 간격) | $(0,4),(1,5),\ldots$ 복사 | 아직 $w_1$ (안 바뀜) |
| $2$ | $(0,2),(1,3),\ldots$ 복사 | 아직 $w_1$ |
| **$1$ (인접)** | **$(0,1)$** 에서 $\hat{w}[1]\leftarrow\hat{w}[0]$ | **$=\hat{w}[0]=w_0$** |

$\hat{w}[1]$ 은 **마지막 stage ($\mathrm{len}=1$)** 의 쌍 $(0,1)$ 때문에 $w_0$ 과 같아진다.  
($\hat{w}[2]$ 는 더 이른 stage 에서 이미 $\hat{w}[0]$ 을 받아 둔 뒤, $\mathrm{len}=1$ 에서 이웃과 맞춰진다.)

---

<!-- source: DIL-11-U1 | z=0 n=8 numeric -->
<!-- _class: tiny -->
## $z=0$ 전파 예제 ($n=8$, 모든 twiddle $0$)

**출처:** Algorithm 41 과 동일한 제어 흐름 · $n=8$ 으로 축소한 예.

초기 (입력 계수 복사 후):

$$
\hat{w}=[42,\;7,\;5,\;9,\;3,\;1,\;8,\;4]
$$

| 직후 stage | 배열 $\hat{w}$ (모든 $z=0$) | 비고 |
|------------|------------------------------|------|
| $\mathrm{len}=4$ | $[42,7,5,9,\;\mathbf{42},7,5,9]$ | $4..7$ 이 $0..3$ 복사 |
| $\mathrm{len}=2$ | $[42,7,\;\mathbf{42},7,\;42,7,\;\mathbf{42},7]$ | 간격 2 복사 |
| $\mathrm{len}=1$ | $[42,\;\mathbf{42},\;42,\;\mathbf{42},\;42,\;\mathbf{42},\;42,\;\mathbf{42}]$ | **$(0,1)$** 등 인접 복사 |

$$
\hat{w}[1]:\quad 7 \xrightarrow{\mathrm{len}=1} 42 = w_0
$$

ML-DSA ($n=256$) 도 동일: $\mathrm{len}=128\to\cdots\to 1$ 을 거치며 **최종적으로 모든 칸이 $w_0$**.

---

<!-- source: DIL-11-U1 | bridge collapse to key recovery -->
## *NTT* 붕괴를 키 복구에 쓰는 조건

**출처:** [11] §6.1.1 *Sign_Fault_NTT_C*; FIPS 204 Alg 7 L17–20.

*NTT* 출력이 한 값으로 반복되는 것만으로는 비밀키가 드러나지 않는다.  
**어느 다항식**에 대해 $\mathrm{NTT}$ 를 오류 내는지가 핵심이다.

| 대상 입력 | 전 *twiddle* $0$ 결과 | 서명식에 미치는 영향 |
|-----------|----------------------|----------------------|
| *challenge* $c$ 이고 **$c_0=0$** | $\hat{c}^*=[0,0,\ldots,0]$ | $c\cdot s_1$ 항이 **사라짐** |
| (참고) *nonce* $y$ | $\hat{y}^*$ 저엔트로피 | 대안 $z$ 구현에서만 $s_1$ 노출 (Attack-2) |

*Sign_Fault_NTT_C* 는 **$\mathrm{NTT}(c)$** 에 오류를 넣고, 정상 서명과 오류 서명의 **차분**으로 $s_1$ 을 얻는다.

---

<!-- source: DIL-11-U1 | bridge recovery steps -->
## Attack-1 경로 요약 (*Sign_Fault_NTT_C*)

**출처:** [11] Eq.(12)–(13); FIPS: $z=y+\langle\langle c s_1\rangle\rangle$.

**전제:** *deterministic* · 동일 메시지 · 동일 $\kappa$ (같은 $y$) · **$c_0=0$.**

1. **정상 실행** (fault 없음)
   $$z = y + c\cdot s_1$$
2. **오류 실행** — $\mathrm{NTT}(c)$ 전 *twiddle* $0$ 이고 $c_0=0$ → $\hat{c}^*=0$
   $$
   \langle\langle c s_1\rangle\rangle^*
   =\mathrm{NTT}^{-1}(\hat{c}^*\circ\hat{s}_1)=0
   \quad\Rightarrow\quad
   z^* = y
   $$
3. **차분** (둘 다 공개 서명에서 관측)
   $$
   \Delta z = z - z^* = c\cdot s_1
   $$
4. $c$ 는 서명 $\tilde{c}$ 에서 *SampleInBall* 로 복원 → (가역이면)
   $$
   s_1 = (\Delta z)\cdot c^{-1}
   $$

오류 서명은 **마스크 $y$ 만** 남기고, 정상 서명과의 차분은 **$c\cdot s_1$** 이 된다.

---

<!-- source: DIL-11-U1 | why c-hat star is zero -->
## $\hat{c}^*=0$ 은 어떻게 보장되나?

**출처:** [11] §6.1.1 (Attack-1).

> *“The message $m$ is chosen such that the first coefficient of challenge $c$ is 0 (i.e.) $c_0 = 0$. The attacker yet again lets the target sign $m$, but this time, the NTT of $c$ is faulted to zeroize all its twiddle constants. As a result, the faulty $c^* = (c_0, 0, 0, \ldots, 0)$. Since $c_0 = 0$, the faulty challenge $c^* = 0$.”*

| 단계 | 내용 |
|------|------|
| 1 | 메시지 $m$ 을 골라 *challenge* 가 **$c_0=0$** 이 되게 함 |
| 2 | 동일 $m$ 을 다시 서명하며 $\mathrm{NTT}(c)$ 의 *twiddle* 을 전부 0 으로 |
| 3 | $c_0=0$ 이므로 오류 *challenge* $c^*=0$ → $z^*=y$ |

*Fault* 만으로는 영벡터가 되지 않는다. 논문은 **$c_0=0$ 이 되도록 메시지를 고른 뒤** *NTT* 오류를 넣는다.

---

<!-- source: DIL-11-U1 | c0 paper + FIPS view -->
<!-- _class: tiny -->
## $c_0=0$ 과 *fault* 의 역할

**출처:** [11] §6.1.1; FIPS 204 Algorithm 41 ($z=0$ → 출력 $=w_0$ 반복).

| 조건 | 결과 |
|------|------|
| *Fault* 만 ($\mathrm{NTT}$ *twiddle* 전 0) | $\hat{c}^*[i]=c_0$ (첫 계수 반복). $c_0\neq 0$ 이면 **비영** |
| **$c_0=0$** + 동일 *fault* | $\hat{c}^*=0$ → $c\cdot s_1$ 항 소멸 → $z^*=y$ |

[11] 표기: 오류 후 $c^*=(c_0,0,\ldots,0)$; $c_0=0$ 이면 $c^*=0$.  
*Verification-Bypass* (§6.2) 도 “$c_0=0$ 이면 $\hat{c}^*=0$” 을 같은 방식으로 사용한다.

---

<!-- source: DIL-11-U1 | 구현 한계 -->
## [11] 한계 — *implementation dependence*

**출처:** [11] 실험 설정 (*pqm4*, Cortex-M4, *EMFI*); FIPS 204는 *twiddle* 적재 방식을 규정하지 않음.

*Fault injection* 과 *side-channel* 공격의 성패는 **구현**에 크게 좌우된다.

| 한계 | 설명 |
|------|------|
| *Twiddle* 적재 방식 | 포인터·테이블·*on-the-fly* 계산에 따라 공격면이 달라짐 |
| 단일 fault → 전 *twiddle* 0 | 표준이 강제하지 않음 · [11]의 특정 DUT/바이너리에서 관찰 |
| 캐시로 모듈 내 *NTT* 전파 | 논문이 제시한 **가설** · 마이크로아키텍처 의존 |
| 대응 구현 | *integrity check*, jitter, on-the-fly *zetas* 등으로 공격이 실패할 수 있음 |

---

<!-- source: DIL-11-U1 | Sign NTT sites -->
## *Sign_internal* 에서 *NTT* 가 불리는 곳 (FIPS Alg 7)

| Alg 7 | 연산 | 비고 |
|-------|------|------|
| L2–4 | $\mathrm{NTT}(s_1),\,\mathrm{NTT}(s_2),\,\mathrm{NTT}(t_0)$ | 루프 밖 |
| L12 | $\mathrm{NTT}^{-1}(\hat{A}\circ\mathrm{NTT}(y))$ | 매 루프 · *nonce* $y$ |
| **L17** | $\hat{c}\leftarrow\mathrm{NTT}(c)$ | 매 루프 · *challenge* ← **Attack-1 타겟** |
| L18–19, 25 | 관련 $\mathrm{NTT}^{-1}$ | $c s_1$ 등 |

*Verify_internal* (Alg 8 L8–9): $\mathrm{NTT}(c)$ 등 — *verification bypass* 후보

L16 *SampleInBall* 로 $c$ 가 sparse 이어도, FIPS 204는 L17에서 $\mathrm{NTT}$ 를 **생략하지 않는다**.

---

<!-- source: DIL-11-U1 | 불일치 판정 -->
## [11] 논문 표기와 FIPS 204 — 대조

| 불일치 | 공격 추적 | 요지 유지? |
|--------|-----------|------------|
| $\sigma$에 $c$ vs $\tilde{c}$ | $\tilde{c}\mapsto c=\textit{SampleInBall}(\tilde{c})$ | **유지** |
| $c\leftarrow H$ vs *SampleInBall* | $c_0=0$ 검사를 샘플 이후로 | **유지** |
| 라인/함수명 | 대응표 | **유지** |
| **대안 $z$ 경로 (Attack-2)** | FIPS 기본 $z=y+\langle\langle c s_1\rangle\rangle$ 와 불일치 | **Attack-2만 조건부** |
| *twiddle-pointer* FI | 구현 의존 | 대수 핵은 유지 |

*Sign_Fault_NTT_C* (Attack-1) 은 FIPS 기본 *Sign* 경로와 정합한다.  
*Sign_Fault_NTT_Y* (Attack-2) 는 대안 $z$ 구현을 전제로 한다.

---

<!-- source: DIL-11-U2 | Attack-1 | [11] §6.1.1 -->
## [11] Attack-1 — *Sign_Fault_NTT_C* 개요

**출처:** [11] §6.1.1; FIPS 204 Algorithm 7 L15–20, Algorithm 2 (*deterministic*), Algorithm 41.

위에서 본 *NTT* 붕괴·$c_0=0$·차분 복구를, 표준 *Sign* 기호로 다시 적는다.

| 항목 | 내용 |
|------|------|
| 이름 | *Sign_Fault_NTT_C* |
| 모드 | **deterministic** *signing* only |
| 대상 | *challenge* 의 $\mathrm{NTT}(c)$ (Alg 7 **L17**) |
| 오류 | 해당 *NTT* 에서 전 *twiddle* $z=0$ (Alg 41 L10) |
| 전제 | 동일 메시지, 동일 *rejection* 횟수 $\kappa$; $c_0=0$ |

---

<!-- source: DIL-11-U2 | 정상 경로 -->
<!-- _class: code-tiny -->
## [11] Attack-1 — 정상 경로 (FIPS Alg 7)

**출처:** FIPS 204 Algorithm 7 (발췌).

```
15:  c̃ ← H(μ || w1Encode(w1), λ/4)
16:  c  ← SampleInBall(c̃)
17:  ĉ  ← NTT(c)                 ◁ fault 대상
18:  ⟨⟨c s1⟩⟩ ← NTT^{-1}(ĉ ∘ ŝ1)
20:  z  ← y + ⟨⟨c s1⟩⟩
```

대수적으로 (성분 다항식):

$$
z \;=\; y + c\cdot s_1
$$

서명에 실린 $\tilde{c}$ 로부터 $c=\textit{SampleInBall}(\tilde{c})$ 로 *challenge* 를 복원한다.

---

<!-- source: DIL-11-U2 | 오류 효과 -->
## [11] Attack-1 — 오류가 만드는 값

**출처:** [11] Eq.(12)–(13); FIPS Alg 41 ($z=0$) + Alg 7 L17–20.

조건: $c_0=0$ 이고 $\mathrm{NTT}(c)$ 의 전 *twiddle* 이 0.

$$
\hat{c}^*[i] = c_0 = 0 \quad(\forall i)
\qquad\Rightarrow\qquad
\hat{c}^*=0
$$

$$
\langle\langle c s_1\rangle\rangle^*
= \mathrm{NTT}^{-1}(\hat{c}^*\circ\hat{s}_1)=0,
\qquad
z^* = y + 0 = y
$$

| | 정상 | 오류 (동일 $y$, 동일 $\kappa$) |
|--|------|-------------------------------|
| $\hat{c}$ | 정상 *NTT* | $0$ |
| $z$ | $y+c s_1$ | $z^*=y$ |

---

<!-- source: DIL-11-U2 | 키 복구 -->
## [11] Attack-1 — 키 복구

**출처:** [11] §6.1.1; $\Delta\kappa=0$ 일 때.

$$
\Delta z = z - z^* = (y + c s_1) - y = c\cdot s_1
$$

$c$ 가 가역이면

$$
s_1 = (\Delta z)\cdot c^{-1} \quad\text{in } R_q
$$

($\mathbf{s}_1\in R_q^\ell$ 는 성분별로 동일 논리 — [11].)

| 조건 | 내용 |
|------|------|
| $\Delta\kappa=0$ | 정상·오류 *rejection* 횟수 일치 필요 |
| $c_0=0$ | **[11] §6.1.1:** 메시지 $m$ 을 그렇게 선택 |
| $c^{-1}$ | sparse $c$ 가 항상 unit 은 아님 → 실패 시 다른 샘플 |
| 모드 | *deterministic* only (*randomized* 차분 불가) |

---

<!-- source: DIL-11-U2 | 한계 -->
<!-- _class: tiny -->
## [11] Attack-1 — 수치·한계·대응

**출처:** [11] §6.1.1 시뮬레이션·대응 서술.

| 항목 | 논문 서술 | 비고 |
|------|------|----------------|
| 필요 서명 수 | 평균 **≈13**, 1000키, **100%** | *perfect fault* 가정 · 실측 *EMFI* 성공률과 동일시 금지 |
| 오류 서명 | 대개 **invalid** | *Verify_After_Sign* 이 유효한 대응 ([11]) |
| *twiddle* 전 zeroize | *pqm4* + *EMFI* (M4) | **구현 의존** |
| FIPS 대응 | $z=y+\langle\langle c s_1\rangle\rangle$ 와 정합 | 서명 필드 $\tilde{c}$ 에서 $c$ 복원 |

---

<!-- source: DIL-11-U3 | Attack-2 | [11] §6.1.2 -->
## [11] Attack-2 — *Sign_Fault_NTT_Y* 개요

**출처:** [11] §6.1.2.

| 항목 | 내용 |
|------|------|
| 이름 | *Sign_Fault_NTT_Y* |
| 대상 | *nonce* $y$ 의 $\mathrm{NTT}(y)$ (전 *twiddle* $z=0$) |
| 모드 | *probabilistic* / *deterministic* 모두 (논문) |
| 핵심 전제 | $z$ 를 **NTT 영역에서** $y$ 와 결합하는 **대안 구현** |

FIPS 204 Algorithm 7 기본 경로($z\leftarrow y+\langle\langle c s_1\rangle\rangle$)와 **다름**.

---

<!-- source: DIL-11-U3 | z paths -->
## [11] Attack-2 — 두 가지 $z$ 계산

**출처:** [11] Eq.(14); FIPS 204 Algorithm 7 L18–20.

| 경로 | 식 | 비고 |
|------|-----|------|
| **FIPS 기본** · 다수 구현 | $z = y + \mathrm{NTT}^{-1}(\hat{c}\circ\hat{s}_1)$ | $y$ 는 *normal domain* 가산 |
| **대안** ([11]) | $z = \mathrm{NTT}^{-1}(\hat{s}_1\circ\hat{c}+\hat{y})$ | *Skip_Add* 대응·메모리 절약 동기 |

[11]: 대안을 쓰는 **공개 구현은 알지 못함**.  
$\mathrm{NTT}(y)$ 에 fault 를 넣어도, **기본 경로**에서는 $z$ 가 저엔트로피 $y$ 로 바뀌지 않는다.

---

<!-- source: DIL-11-U3 | fault effect -->
## [11] Attack-2 — 오류 시 $z^*$ (대안 경로)

**출처:** [11] Eq.(15). 전제: 대안 $z$ 구현 + $\mathrm{NTT}(y)$ *twiddle* 전 zeroize.

$\hat{y}^*$ 가 저엔트로피일 때 (단일 다항식, $sc = c\cdot s$):

$$
z^*[i] =
\begin{cases}
sc[i] + y[i], & i=0 \\
sc[i], & 1 \le i < n
\end{cases}
$$
<div class="takeaway">$sc$ 의 **거의 모든 계수**가 $z^*$ 에 노출.</div>

첫 계수는 추측 후 $\ell_\infty(s)$ 범위로 진위 판별 ([11]).

*Rejection* 루프의 **첫 반복**에서 $\mathrm{NTT}(y)$ 가 고정 시점에 있어 조준이 가능하다고 서술 ([11]).

---

<!-- source: DIL-11-U3 | recovery limits -->
<!-- _class: tiny -->
## [11] Attack-2 — 복구·수치·한계

**출처:** [11] §6.1.2.

| 항목 | 논문 서술 | 비고 |
|------|------|----------------|
| 키 복구 | 노출된 $sc$ + 소수 추측 → $s_1$ | 대안 $z$ 경로 **전제** |
| 서명 수 | 평균 **≈3**, 1000키, *perfect fault* | 실측 *EMFI* 성공률과 동일시 금지 |
| 오류 서명 | **valid** (*verify* 통과 가능) | *Verify_After_Sign* **무력** ([11]) |
| FIPS 기본 경로 | — | 대안 $z$ 구현이 아니면 **적용되지 않음** |
| 구현 | *twiddle-pointer* *EMFI* | 구현·보드 의존 |

---

<!-- source: DIL-11-U4 | Verify-Bypass | [11] §6.2 -->
## [11] *Verification-Bypass* — 개요

**출처:** [11] §6.2; FIPS 204 Algorithm 8 (*Verify_internal*).

| 항목 | 내용 |
|------|------|
| 목표 | invalid 서명을 *verify* 가 **수락**하도록 강제 |
| 대상 | 검증 중 $\mathrm{NTT}(c)$ · 전 *twiddle* $z=0$ |
| 조건 | $c_0=0$ → $\hat{c}^*=0$ |
| 비밀키 | **불필요** (위조·수락 강제) |

---

<!-- source: DIL-11-U4 | effect -->
## [11] *Verification-Bypass* — 오류 효과

**출처:** [11] Eq.(16); FIPS Alg 8 에서 $\mathrm{NTT}(c)$ 사용.

$\hat{c}^*=0$ 이면 검증 측 *commitment* 재구성이 $(z,h)$ 중심으로 붕괴한다 (논문 표기):

$$
w_1^* = \mathrm{UseHint}(h,\, A\cdot z)
$$

$$
c^* \;\text{(또는 } \tilde{c}^*\text{)} \;=\; H(\mu \| w_1^*)
$$

$w_1^*$ 는 공격자가 고른 $(z,h)$ 의 함수이므로, 재계산 *challenge* 를 공격자가 맞출 수 있다.

---

<!-- source: DIL-11-U4 | malicious + attack -->
## [11] *Verification-Bypass* — 악성 서명·공격 단계

**출처:** [11] §6.2, Alg.4 (의도에 맞게 해석).

1. 규범 조건을 만족하는 $(z^*, h^*)$ 샘플  
2. $w_1^* \leftarrow \mathrm{UseHint}(h^*,\, A z^*)$ (논문 표기)  
3. $c^*$ (FIPS: $\tilde{c}$) 유도 — **$c_0^*=0$** 될 때까지 재시도  
4. $\sigma^*=(z^*,h^*,c^*)$ (FIPS 인코딩: $(\tilde{c},z,h)$)  
5. *Verify*$(\sigma^*,\mu)$ 중 $\mathrm{NTT}(c^*)$ 에 *fault* → $\hat{c}^*=0$ → **accept**

논문: 1000 메시지 시뮬레이션, *perfect fault* 가정 하 **100%**.

---

<!-- source: DIL-11-U4 | limits -->
<!-- _class: tiny -->
## [11] *Verification-Bypass* — 한계·FIPS 대조

**출처:** [11] §6.2; FIPS 204 Alg 8.

| 항목 | 내용 |
|------|------|
| $\sigma$ 표기 | 논문 $(z,h,c)$ vs FIPS $(\tilde{c},z,h)$ · *SampleInBall* 로 $c$ 복원 |
| Alg.4 루프 조건 | 본문은 “$c_0=0$ 될 때까지”이나 의사코드 `while c0 = 0` 과 **표기 모순** 가능 |
| FIPS 검증식 | $Az - c t_1\cdot 2^d$ 후 *UseHint*; $\hat{c}=0$ 이면 $c$ 항 소멸 계열 |
| *twiddle* FI | 구현·보드 의존 |
| 요지 | *challenge NTT* 붕괴로 검증 수락 강제 |

---

<!-- source: DIL-11-U5 | summary -->
<!-- _class: tiny -->
## [11] 정리

**출처:** [11]; FIPS 204 Alg 7·8·41.

| 경로 | 주입 대상 | 결과 요지 | FIPS 기본 *Sign* |
|------|-----------|-----------|------------------|
| *Sign_Fault_NTT_C* | $\mathrm{NTT}(c)$ | $z^*=y$ → $\Delta z=c s_1$ → $s_1$ | 정합 (*deterministic*) |
| *Sign_Fault_NTT_Y* | $\mathrm{NTT}(y)$ | 저엔트로피 $y$ 로 $s_1$ 노출 | 대안 $z$ 구현일 때만 |
| *Verification-Bypass* | Verify $\mathrm{NTT}(c)$ | invalid 서명 수락 강제 | $\tilde{c}$ 표기에 맞게 이식 가능 |

공통: *twiddle* 전 $0$ → *NTT* 출력 붕괴 (Alg 41).  
공통 한계: *EMFI*·*twiddle-pointer* 성공은 **구현 의존**.

---

<!-- source: transition to [9] -->
<!-- _class: tiny -->
## 다음 문헌 — [9]

[11] 은 **변환(*NTT*) 내부 상수(*twiddle*)** 를 건드린다.  
[9] 는 **서명 마스크 $\mathbf{y}$ 샘플링** 에서 *instruction skip* 으로 성분 간 등식을 만든다.

둘 다 공개 서명 $\mathbf{z}$ 와 *challenge* $c$ 를 쓰지만, **오류를 넣는 위치**가 다르다.

---

<!-- source: REF-09 -->
## [9] 개요

**출처:** [9] Abstract (TCHES 2023)

> *“… a differential fault attack on the randomized and deterministic versions of CRYSTALS-Dilithium. … requires a few instruction skips and is able to reduce the MLWE problem … to a smaller RLWE problem …”*

| 항목 | 논문 주장 |
|------|-----------|
| 대상 | *CRYSTALS-Dilithium* · *deterministic* **및** *randomized* |
| 수단 | 소수 *instruction skip* |
| 효과 | *MLWE* → 작은 *RLWE* → 격자 해법 |
| 가속 | *hints* + LWE with side-information |
| 추가 | 알고리즘 대응 (재계산·norm 탐지 등) |

---

<!-- source: [9] roadmap | audience -->
<!-- _class: tiny -->
## [9] 읽기 순서

| 단계 | 내용 |
|------|------|
| 1 | *ExpandMask* 가 만드는 *nonce* $\mathbf{y}$ (FIPS Alg 34) |
| 2 | nonce 증가 *instruction skip* → $y[i]=y[j]$ |
| 3 | $z[i]-z[j]=c(s_1[i]-s_1[j])$ 차분 수집 ($\ell-1$ 개) |
| 4 | 공개 $A,\mathbf{t}$ 와 결합 → MLWE를 RLWE로 축소 후 *BKZ* |

---

<!-- source: DIL-09-U1 | FIPS Alg 34 | unmodified -->
<!-- _class: code-tiny -->
## FIPS 204 — Algorithm 34 $\mathrm{ExpandMask}(\rho,\mu)$

**출처:** NIST FIPS 204, §7. Algorithm 34.

**Algorithm 34** $\mathrm{ExpandMask}(\rho,\mu)$  
Samples a vector $\mathbf{y}\in R_q^\ell$ such that each polynomial $\mathbf{y}[r]$ has coefficients between $-\gamma_1+1$ and $\gamma_1$.

**Input:** A seed $\rho\in\mathbb{B}^{64}$ and a nonnegative integer $\mu$.  
**Output:** Vector $\mathbf{y}\in R_q^\ell$.

```
 1: c ← 1 + bitlen(γ1 − 1)                 ▷ γ1 is always a power of 2
 2: for r from 0 to ℓ − 1 do
 3:     ρ' ← ρ || IntegerToBytes(μ + r, 2)
 4:     v ← H(ρ', 32c)                     ▷ seed depends on μ + r
 5:     y[r] ← BitUnpack(v, γ1 − 1, γ1)
 6: end for
 7: return y
```

*Sign_internal* (Alg 7 L11): $\mathbf{y}\leftarrow\mathrm{ExpandMask}(\rho'',\kappa)$.  
성분 $r$ 의 시드는 **$\mu+r$** 에 의존한다.

---

<!-- source: DIL-09-U1 | what is ExpandMask / y -->
## $\mathrm{ExpandMask}$ 가 만드는 것 — *nonce* $\mathbf{y}$

**출처:** FIPS 204 Alg 7 L11–20; [9] 서명식.

$$
\mathbf{z} = \mathbf{y} + c\cdot \mathbf{s}_1
$$

| 기호 | 의미 |
|------|------|
| $\mathbf{y}\in R_q^\ell$ | *ExpandMask* 가 샘플링하는 **마스킹 *nonce*** (다항식 **벡터**, 길이 $\ell$) |
| $\mathbf{y}[i]$ | $i$ 번째 **다항식** (계수가 한 개 스칼라가 아님) |
| $c\cdot\mathbf{s}_1$ | *challenge* 와 비밀 $\mathbf{s}_1$ 의 곱 |
| $\mathbf{z}$ | 서명에 실리는 응답 |

*ExpandMask* 는 $y$ 를 만든다.  
$y$ 는 매 서명(·*rejection* 시도)마다 바뀌는 일회성 마스크이다.

---

<!-- source: DIL-09-U1 | [9] fault target -->
## [9] 주입 대상 — nonce 증가 *skip*

**출처:** [9] §3.1, Fig.1 (`polyvecl_uniform_gamma1`); FIPS Alg 34 L2–3.

구현은 각 성분에 대해 nonce 를 올리며 *ExpandMask* 를 호출한다 (논문 C/asm):

$$
y[i] \leftarrow \mathrm{ExpandMask}(\rho',\, \kappa\cdot\ell + i)
$$

| 항목 | 내용 |
|------|------|
| **Fault** | 루프에서 **nonce 증가 명령 *instruction skip*** (Fig.1 빨간 줄, `adds r4, #1`) |
| **효과** | 연속 두 성분에 **동일 nonce** → $y[i]=y[j]$ (예: $y[0]=y[1]$) |
| **FIPS 대응** | Alg 34 의 $\mu+r$ 증가가 구현의 nonce++ 에 해당 |
| **한계** | [9] 는 이 *skip* 의 **실측을 보고하지 않음** (모델·시뮬레이션; 실현 가능성은 타 문헌 인용) |

---

<!-- source: DIL-09-U1 | numeric nonce skip -->
<!-- _class: tiny -->
## nonce *skip* 이 $\mathbf{y}$ 에 하는 일 ($\ell=4$ 예)

**출처:** Alg 34; [9] Fig.1 · §3.1.

$\kappa=0$, $\ell=4$ 일 때 정상 nonce 열 $0,1,2,3$.

| | nonce 열 | $\mathbf{y}$ 의 성분 |
|--|----------|----------------------|
| 정상 | $0,1,2,3$ | $y[0],y[1],y[2],y[3]$ **서로 다른** 다항식 |
| $0{\to}1$ 증가 *skip* | $0,\;\mathbf{0},\;2,\;3$ | **$y[0]=y[1]$** (같은 다항식), $y[2],y[3]$ 는 그대로 독립 |

### 정리

| 오해 | 정정 |
|------|------|
| $\mathbf{y}$ **전체**가 한 값으로 통일 | **아님.** 보통 **일부 쌍**만 동일 ($y[i]=y[j]$) |
| 공격자가 그 공통 $y$ 값을 **안다** | **아님.** 공통 값 자체는 비밀·난수 |
| 그래도 키가 새는 이유 | $z[i]-z[j]$ 에서 $y$ 가 **상쇄**되어 $c(s_1[i]-s_1[j])$ 만 남음 |

$$
\begin{aligned}
z[i] &= y[i] + c\cdot s_1[i] \\
z[j] &= y[j] + c\cdot s_1[j] \\
y[i]=y[j] &\Rightarrow z[i]-z[j] = c\,(s_1[i]-s_1[j])
\end{aligned}
$$

---

<!-- source: REF-09 B -->
## [9] 키 복구 (1/2) — 차분 관계

**출처:** [9] §3; FIPS 204 Alg 7 — $\mathbf{z}=\mathbf{y}+c\mathbf{s}_1$.

$y[i]=y[j]$ 이면

$$
\mathbf{z}[i]-\mathbf{z}[j]
= c\,(\mathbf{s}_1[i]-\mathbf{s}_1[j])
$$

$c$ 는 서명에 포함(·FIPS 에선 $\tilde{c}$ 에서 복원)되므로, 대개

$$
\mathbf{s}_1[i]-\mathbf{s}_1[j]
= c^{-1}\,(\mathbf{z}[i]-\mathbf{z}[j])
$$

| 항목 | 내용 |
|------|------|
| 한 번의 성공 fault (서명 1개) | 보통 **한 쌍** 관계 (예: $s_1[0]-s_1[1]$) |
| 전체 $\mathbf{s}_1$ 복구에 필요 | **독립 관계 $\ell-1$ 개** ([9] §3.2) |
| 성공 판별 | $\mathbf{z}[0]-\mathbf{z}[1]$ 계수가 $[-2\tau\eta,2\tau\eta]$ 에 몰리면 유력 |

---

<!-- source: DIL-09-U2 | multi fault collection -->
<!-- class: small -->

## 여러 번 fault 가 필요한가?

**출처:** [9] §3.1–3.2.

**예.** 목표는 서로 독립인 차분

$$
s_1[0]-s_1[1],\;
s_1[0]-s_1[2],\;
\ldots,\;
s_1[0]-s_1[\ell-1]
$$

처럼 **$\ell-1$ 개** (또는 동등한 spanning 집합) 를 모으는 것이다.

| 방법 | 내용 |
|------|------|
| **실무적으로 흔히 가정** | 서명 **시도마다 instruction skip 1회** → 성공 시 관계 1개. 이를 **여러 서명**에 반복 |
| **이론적 한 방** | 한 서명 루프에서 skip **$\ell-1$ 회** → $y[0]=\cdots=y[\ell-1]$ 도 가능 ([9]: 어렵다고 명시) |

서명 모드별 **평균 fault 주입 횟수** 예 ([9], level II–V):

| | randomized (대략) | deterministic (대략) |
|--|-------------------|----------------------|
| 성공 오류 서명 1개 | ~3.8–4.7 회 주입 | ~2.4–3.2 회 주입 |
| $\ell-1$ 개 관계 모을 때까지 | ~11–22 회 | ~7–16 회 |

---

<!-- source: DIL-09-U2 | numeric toy differences -->
<!-- _class: tiny -->
## 수치 예 — 차분으로 $s_1[i]-s_1[j]$ (한 계수 슬라이스)

**출처:** [9] Eq.(2)–(3). 다항식 대신 **한 계수 위치**만 정수로 축소한 예.

비밀 (공격자 모름): $s_1[0]=2,\; s_1[1]=-1,\; s_1[2]=3$.  
쉽게 보려고 $c=1$ (실제로는 희소 다항식 $c$).

**서명 A** — fault 로 $y[0]=y[1]=7$, $y[2]=4$ (공격자는 $y$ 모름):

$$
\begin{aligned}
z[0]&=7+1\cdot 2=9,&
z[1]&=7+1\cdot(-1)=6,&
z[2]&=4+1\cdot 3=7
\end{aligned}
$$

$$
z[0]-z[1]=3=s_1[0]-s_1[1]
$$

**서명 B** — 다른 fault 로 $y[0]=y[2]=5$, $y[1]=1$:

$$
z[0]=7,\; z[2]=8
\quad\Rightarrow\quad
z[0]-z[2]=-1=s_1[0]-s_1[2]
$$

모인 것:

$$
s_1[0]-s_1[1]=3,\qquad s_1[0]-s_1[2]=-1
$$

$\ell=3$ 이면 관계 **2($=\ell-1$)** 개.  
아직 $s_1[0]$ 자체는 모름 → 공개식 $\mathbf{t}=A\mathbf{s}_1+\mathbf{s}_2$ 와 묶어 **격자 문제 축소** ([9] §3.2).

---

<!-- source: REF-09 B | lattice -->
## [9] 키 복구 (2/2) — MLWE → RLWE

**출처:** [9] §3.2–§4; FIPS 204 Alg 6 — $\mathbf{t}=\mathbf{A}\mathbf{s}_1+\mathbf{s}_2$, $\hat{\mathbf{A}}\leftarrow\mathrm{ExpandA}(\rho)$.

### 누가 공개인가?

| 기호 | 공개? | 이유 |
|------|-------|------|
| $\rho$ | **공개** | 공개키 $pk$ 에 포함 (Alg 6 L8 `pkEncode`) |
| $\mathbf{A}$ | **공개** | $\mathrm{ExpandA}(\rho)$ 로 **누구나 재생성** |
| $\mathbf{t}$ 또는 $\mathbf{t}_1$ | **공개** (표준은 $\mathbf{t}_1$) | MLWE 인스턴스 |
| $\mathbf{s}_1,\mathbf{s}_2,\mathbf{t}_0$ | **비밀** | 개인키 |

차분으로 $\lambda[j]=s_1[0]-s_1[j+1]$ 등을 알면, $\mathbf{s}_1$ 을  
“**한 다항식 $s_1[0]$ + 알려진 차분**” 으로 쓸 수 있다.

$$
\mathbf{s}_1
=
\bigl(s_1[0],\;
s_1[0]-\lambda[0],\;
s_1[0]-\lambda[1],\;
\ldots\bigr)
$$

이를 $\mathbf{t}=A\mathbf{s}_1+\mathbf{s}_2$ 에 대입하면  
**모듈 MLWE $(k,\ell)$** 이 **더 작은 RLWE 형** 문제로 줄어든다 ([9]).

| 단계 | 내용 |
|------|------|
| 1 | fault 서명들로 $\ell-1$ 개 독립 차분 수집 |
| 2 | $c^{-1}(z[i]-z[j])$ 로 $s_1[i]-s_1[j]$ |
| 3 | $\mathbf{t}$·$A$ 와 결합 → 축소 격자 |
| 4 | *lattice reduction* (BKZ 등) 으로 $s_1[0]$ 등 복구 후 차분으로 나머지 전개 |
| 5 | (선택) *hints* / side-information 으로 가속 (§5) |

$t$ 전체가 공개일 때와 $t_1$ 만 공개일 때 난이도가 다르다 ([9]).

---

<!-- source: DIL-09-U2 | is lattice easy -->
## 축소 후 격자 문제는 “쉬운가”?

**출처:** [9] §3.2, §4, Table 2.

### 정리

| 질문 | 답 |
|------|-----|
| $s_2$ 를 몰라도 되는가? | **예 (축소 단계).** 식은 $s_1[0]$ 과 $s_2[0]$ 등 **소수의 다항식** 만 남김 ([9] Eq.(6): RLWE $(1,1)$, $n=256$) |
| $s_1$ 을 닫힌 식으로 바로 쓰나? | **아니요.** 차분으로 “$s_1[0]$ + 알려진 $\lambda$” 형태로 **표현**만 바꿈 |
| 그 문제는 잘 알려진가? | **예.** *Search-LWE* / *RLWE* → *BKZ* 격자 축소 (암호 표준 도구) |
| 계산 난이도 | 원 MLWE 보다 **훨씬 낮고**, level II/V 는 논문이 **수십 시간** 규모로 해법 보고. 사칙 수준은 아님 |

### [9] Table 2 수치 ($t$ 공개 가정, post-attack)

| NIST level | 공격 전 추정 $\beta$ (MLWE) | 공격 후 추정 $\beta$ (RLWE) | 구체 해법 (논문) |
|------------|---------------------------|---------------------------|------------------|
| II | ~434 | ~**62** | 평균 **~40시간**, 성공 100% (10회) |
| III | ~641 | ~**68** | 추정만 (저자 환경에선 시간 부담) |
| V | ~890 | ~**62** | II 와 동형 인스턴스 · 유사 해법 |

$\beta$ 가 수백 → 약 60 으로 떨어지면 **암호학적 안전 영역 밖**으로 보지만, 여전히 **고성능 격자 축소**가 필요하다.

$t_1$ 만 공개($t_0$ 비밀)이면 축소 RLWE 가 **더 어려워진다** ([9] §3 말미·§5.3).  
$s_1$ 만 알아도 위조 경로가 있다는 기존 결과도 논문이 인용한다.

---

<!-- source: REF-09 C–G -->
## [9] 서명모드·횟수·한계

| 항목 | 내용 |
|------|------|
| **서명 모드** | det + rand; abort 고려; rand는 주로 **첫 시도** *fault* |
| **오류 횟수** | 평균 inject: rand ~11–22 / det ~7–16 (level II–V, $\ell-1$ 관계 필요) |
| **공격 실증** | SW+ASM 지점 제시; **실제 글리치 실험 없음** |
| **HAETAE 연계** | *y*-경로 유사 **가능**, 대상 논문 본문에서 대조 |
| **한계** | full $\mathbf{t}$ vs secret $\mathbf{t}_0$; 대응: 재계산·norm 탐지 |

---

<!-- source: REF-10 -->
## [10] 개요

**출처:** [10] Abstract (TCHES 2024)

> *“… two new key-recovery fault attacks on randomized/hedged Dilithium. Both attacks are based on the idea of correcting faulty signatures after signing.”*

| 항목 | 논문 주장 |
|------|-----------|
| 대상 | *randomized* / *hedged Dilithium* |
| 핵심 | *Correction* — 오류 서명 보정으로 비밀 중간값 회수 |
| 공격 | (1) $z$ 경로 *skip* 확장 · (2) 공개 행렬 $A$ *fault* |
| 검증 | 시뮬레이션 + ARM 클럭 글리치 |

---

<!-- source: REF-10 -->
## [10] Correction이란?

**출처:** [10] 본문이 정의하는 *Correction* 공격 절차 (vs 고전 *DFA*).

고전 *DFA*: 동일 **$y$** 의 정상/오류 **두 번** 서명 (결정론에 유리)

**본 논문 *Correction*:**

1. 서명 루틴 **한 번** 호출 + fault → 대개 **verify 실패**
2. 선택한 중간값 후보로 서명(또는 검증 입력)을 **수정**
3. **verify 성공**할 때까지 탐색 → 그 값 = 키 관련 정보
4. 다수 수집 후 선형대수/격자로 **$s_1$**

---

<!-- source: REF-10 Attack1 -->
## [10] 공격 1 — Skip @ $\mathbf{z}=\mathbf{y}+c\mathbf{s}_1$

**출처:** [10] 공격 1 서술 + 서명 식 $\mathbf{z}=\mathbf{y}+c\mathbf{s}_1$ (FIPS Alg 7 L20 계열).

**A. 대상**

* $\mathbf{z}$ 계산 시 **한 계수**에 대한 **$cs_1$ 덧셈 skip**
* 결과: 그 위치 $z' \approx y$ ($cs_1$ 항 누락)

**B. 로직**

1. 오류 서명 $(c,z',h)$ 획득
2. 후보 $\alpha \approx (c s_1)_j[i]$ 를 $z'$에 더하며 **verify**
3. 성공 $\alpha$ → **$s_1$ 선형식 1개**
4. 성분별 충분한 식 → **$s_1$ 복구**

Dilithium2: 대략 **~1024** faulty signatures (abstract)

---

<!-- source: REF-10 Attack2 -->
## [10] 공격 2 — Fault @ 공개 행렬 $\mathbf{A}$

**출처:** [10] 공격 2 — *ExpandA* / 공개 행렬 $\mathbf{A}$ 계수 *fault* (논문 본문).

**A. 대상**

* **ExpandA($\rho$)**: 공개 $\mathbf{A}$ 의 **한 계수** 오류 ($\Delta A$ 알고 있음)
* bit-flip / zeroing / 알려진 값 주입 등
* $\mathbf{A}$ 는 공개 → 부채널 보호가 약할 수 있는 지점

**B. 로직**

1. 오류 $\mathbf{A}'$ 로 서명 → 검증 실패
2. 검증식에서 $? \approx \Delta A\cdot\mathbf{y}$ 형태를 **열거**
3. 올바른 $?$ → **$y$ 정보** → **$s_1$** 쪽으로 연결
4. 다수 샘플로 키 복구

Dilithium2: 대략 **~512** faulty signatures (abstract)

---

<!-- source: REF-10 C–G -->
## [10] 서명모드·횟수·한계

| 항목 | 내용 |
|------|------|
| **서명 모드** | *hedged*/*rand*; 서명당 1 *fault*; abort 시 첫 시도 전략으로 비용 보정 |
| **오류 횟수** | ~1024 / ~512 (공격1/2, Dilithium2 abstract) |
| **공격 실증** | **시뮬레이션 + ARM 클럭 글리치** |
| **HAETAE 연계** | *unpackA* / *seed_A*·서명 경로와 **개념 비교 가능** (수치 단정 X) |
| **한계** | shuffle·mask·sign-then-verify 등; *ineffective fault* 우회는 비용↑ |

---

<!-- source: REF-12 -->
## [12] 개요

**출처:** [12] Abstract (FDTC 2024)

> *“a fault injection attack on hedged ML-DSA … the secret key vector $s_1$ is derived directly from the resulting faulty signature.”*

| 항목 | 논문 주장 |
|------|-----------|
| 대상 | *Hedged ML-DSA* |
| 결과 | **1** faulted signature → $\mathbf{s}_1$ (~**53%**) |
| 장비 | *ChipWhisperer-Husky* + *STM32F4* |
| 특징 | 산출 서명 *verify* 통과 가능 |

---

<!-- source: REF-12 A -->
## [12] 주입 대상 — $\rho'$ *SHAKE absorb*

**출처:** [12] 공격 서술 + *hedged* 추가 구현 · crowbar *voltage glitch*

| | 내용 |
|--|------|
| 알고리즘 | *Hedged* 시드 $\rho'$ ← $H$(키·메시지·난수 관련) |
| 구현 타겟 | *SHAKE256 absorb* (예: `KeccakF1600_StateXORBytes`) |
| Fault | *Crowbar voltage glitch* → absorb **skip** |
| 효과 | $\rho'$ **고정·예측 가능** |

---

<!-- source: REF-12 B -->
## [12] 키 복구

**출처:** [12] 절차 + 서명 식 $\mathbf{z}=\mathbf{y}+c\mathbf{s}_1$ (FIPS/*Dilithium* 공통)

1. Fault 후에도 서명 **유효(*verify* OK)** 가능 (논문 관찰)
2. 동일 $\rho'$로 **$y$** 재계산
3. 서명 관계:

$$
\mathbf{z} = \mathbf{y} + c\mathbf{s}_1
$$

4. 비밀키 복구:

$$
\mathbf{s}_1 = (\mathbf{z}-\mathbf{y})\,c^{-1}
$$

5. **단일** 성공 서명 → **$s_1$** → existential forgery

> sign-then-verify 는 **valid fault** 를 놓칠 수 있음

---

<!-- source: REF-12 C–G + 스펙트럼 -->
## [12] 서명모드·횟수·한계 · 스펙트럼

| 항목 | 내용 |
|------|------|
| **서명 모드** | *hedged*; 메시지 제어 불필요 |
| **오류 횟수** | **1** sig; ~**53%** 복구 성공 |
| **공격 실증** | CW-Husky crowbar **실측** |
| **HAETAE 연계** | *seed*/*expandYbb* 와 **최근접** (III장 대조) |
| **한계** | *SHAKE* 무결성 필요; *valid-fault* 탐지 어려움 |

**배경 스펙트럼 (출판 순):** [11] *NTT* · [9] *y*-nonce·격자 · [10] *Correction* · [12] **시드 absorb**

---

<!-- source: REF-[9–12] 종합 -->
## Dilithium FI 배경 종합 → HAETAE 공백

**출처:** 참고문헌 [9]–[12], 대상 논문 §I (p.430). *HAETAE* 에 대한 종합 FI 분석은 아직 보고되지 않았다.

| 축 | Dilithium 계 ([9]–[12]) | HAETAE 본 논문 동기 |
|----|-------------------------|---------------------|
| 대상 연산 | y·z·A·NTT·**시드 해시** 등 **다양** | 전체 서명 구조 체계 분석 **부재** |
| 키 복구 | 차분·Correction·격자·**직접 역산** | LSB·unpack·부호·**시드** 네 지점 |
| HW | EMFI·글리치·CW-Husky | SW + **CW-Husky·STM32** 실증 |
| 모드 | det / rand / **hedged** | 본 연구: **deterministic** 중심 |

---

<!-- _class: lead divider -->
# 대상 논문 </br> HAETAE Fault Injection Attacks

*양자 내성 암호 HAETAE에 대한 오류 주입 공격 및 대응 기법*  
Lee · Kim · Ha, Journal of The Korea Institute of Information Security & Cryptology, VOL.36, NO.2, 2026

---

<!-- source: P-002 | §0 요약 | p.429 -->
## 요약 (1/2) — 문제와 연구 공백

**출처:** 대상 논문 **요약** 절 (p.429).

양자 위협에 대응해 **경량화**와 **부채널 내성**을 목표로 제안된 격자 기반 서명 스킴 **HAETAE**는, 수학적 안전성과 별개로 실제 구현 시 **Fault Injection Attack (*FI*)** 에 취약할 수 있다.

특히 **Fiat-Shamir with Aborts** 기반의 **Dilithium**과 구조적으로 유사함에도,

* 전체 서명 구조 대상의 **공격 지점 도출**
* **하드웨어 실증** 연구

는 아직 학계에 보고된 바 없다.

---

<!-- source: P-002 | §0 요약 | p.429 -->
## 요약 (2/2) — 기여

**출처:** 대상 논문 **요약** 절 기여 목록 (p.429).

1. **Deterministic** *HAETAE* 서명 구조를 분석하여 오류 주입 공격 지점 제시
 - **LSB**
 - **공개 행렬 언패킹**
 - **부호 비트**
 - **샘플링 시드** 생성
2. 소프트웨어 및 하드웨어 실험: 단일 또는 소수의 오류 주입만으로 **비밀 키 복구** 가능 확인
3. 제안 대응 기법: **5% 미만** overhead로 공격 완화 입증

---

<!-- _class: lead divider -->
# I. 서론

---

<!-- source: P-006 | §I | p.429–430 -->
## I. 서론 — PQC 표준과 HAETAE

**출처:** 대상 논문 §I 첫 문단 (p.429–430).

양자컴퓨팅 기술의 발전은 소인수분해 및 이산로그 문제에 기반한 기존 공개키 암호체계의 안전성을 근본적으로 위협한다.

* **NIST:** 2016년부터 **Post-Quantum Cryptography (PQC)** 표준화 추진
* **2024년 8월:** 디지털 서명 표준으로 **CRYSTALS-Dilithium (ML-DSA)** 최종 선정 [1]
* **국내 KpqC** (Korean Post-Quantum Cryptography) 공모전
* **2025년** 전자서명 부문: **HAETAE**가 **AIMer**와 함께 최종 후보로 선정

---

<!-- source: P-007 | §I | p.430 -->
## I. 서론 — HAETAE 설계 특징

**출처:** 대상 논문 §I (p.430) · *HAETAE* 원논문 [2].

**HAETAE**[2]: **Module-LWE** 및 **Bimodal Self-Target MSIS** 격자 문제 기반 서명 스킴

* **Bimodal hyperball rejection sampling**
* **고정소수점 최적화**
* → 서명·키 크기를 줄이면서 효율성 확보

특히 **수동적 공격**, 즉 **부채널 공격**에 대한 내성을 목표로 설계되어 실용적 활용 가능성이 높다.

---

<!-- source: P-008 | §I | p.430 -->
## I. 서론 — 구현과 Fault Injection Attack (FI)

**출처:** 대상 논문 §I (p.430) 및 인용 [3]–[8].

수학적 안전성은 실제 **하드웨어 구현**에서 그대로 보장되지 않는다. 
성능 최적화·구현 제약 → 새로운 **공격 표면**.

**Fault Injection Attack (*FI*)** 수단 예:

* 클럭 글리치 [3]
* 전압 글리치 [4]
* 레이저 [5]
* 전자기파 [6]

기존 암호 체계 전반에서 위험이 확인되었다 [7,8]. 
FI는 연산 흐름·내부 데이터를 왜곡하여 비밀 추출·검증 우회가 가능한 **능동적** 공격이다.

---

<!-- source: P-009 | §I | p.430 -->
## I. 서론 — Dilithium FI vs HAETAE 공백

**출처:** 대상 논문 §I (p.430); 참고문헌 [9]–[12].

**Dilithium** (NIST PQC 격자 서명): 다양한 오류 주입 공격 제안. 
단일 또는 다중 오류로 **비밀 키 벡터 전체 복구**가 실험적으로 입증되었다 ([9]–[12]).

**HAETAE:** 오류 주입 공격 연구는 **매우 제한적**. 
구조적으로 Dilithium과 유사함에도 **전체 서명 과정**에 대한 종합 FI 분석은 아직 보고되지 않음.

특히 **온라인/오프라인 기반 랜덤화 서명**은 공식 구현·하드웨어 검증이 부족해 현실적 분석에 제약이 있다. 
<div class="takeaway">본 연구가 **deterministic** *HAETAE* 를 대상으로 하는 동기와 연결.</div>


---

<!-- source: P-010 | §I | p.430 -->
## I. 서론 — 본 논문의 기여

**출처:** 대상 논문 §I 기여 서술 (p.430).

**대상:** 결정론적(**deterministic**) **HAETAE**

1. HW 구현 환경의 오류 주입 공격을 **체계적으로 분석**하고 **대응** 제시
2. 서명 내부 연산에서 **네 가지** 공격 지점 도출
 - **LSB**
 - **공개 행렬 언패킹**
 - **부호 비트**
 - **샘플링 시드**
3. 위조 서명에 필요한 **비밀 키 벡터 복구** 가능 확인
4. 실험: SW 오류 삽입 + **ChipWhisperer-Husky** · **STM32F4** 클럭 글리치
5. **알고리즘** 및 **구현** 수준의 경량 대응 기법

---

<!-- _class: lead divider -->
# II. 관련 연구 및 배경 지식

---

<!-- source: P-011 | §2.1 | p.430 -->
## 2.1 HAETAE — 명칭과 설계 목표

**출처:** 대상 논문 §2.1 (p.430).

**HAETAE** = Hyperball bimodAl modulE rejecTion signAture schemE

* **Bimodal hyperball rejection sampling**
* **고정소수점** 연산 기반 구현
* 서명·검증 키 크기 **최대 39%** 축소
* 목표: 서명이 **TCP / UDP** 한 패킷에 포함되며 높은 보안성 유지

---

<!-- source: P-012 | §2.1 | p.430 -->
## 2.1 키 생성 — 요지

**출처:** 대상 논문 §2.1; *HAETAE* [2].

키 생성 의사코드 전체는 여기서 풀지 않는다.  
이후 공격 설명에 필요한 구분만 둔다.

| 구분 | 내용 |
|------|------|
| 공개 | 시드·행렬 등 검증·서명이 공유하는 값 |
| 비밀 | $s_1,s_2$ 등 서명 키 성분 (*MLWE* / *Truncation*) |

세부 단계는 본 논문 §2.1 및 *HAETAE* [2] 를 따른다.

---

<!-- source: P-013 | §2.1 | p.430–431 -->
## 2.1 서명 — $y$ 시드 (공격과의 접점)

**출처:** 대상 논문 **Fig. 2**, §2.1; *HAETAE* [2].

서명 전체 단계는 Fig. 2 / [2] 를 따른다.  
시드 공격·배경 문헌 [12] 와 맞닿는 최소 관계만 적는다.

$$
\mathrm{seed}_{ybb} \leftarrow H(K,\, \mu)
\qquad
(y \leftarrow \mathrm{expandYbb}(\mathrm{seed}_{ybb},\,\ldots))
$$

| 기호 | 의미 |
|------|------|
| $K$ | 비밀 시드 |
| $\mu$ | 메시지 관련 해시 |
| $y$ | *Bimodal* 이산 하이퍼볼 샘플 (Fig. 1) |

---

<!-- _class: lead divider -->
# III. HAETAE 서명 알고리즘 </br> 오류 주입 공격

1. 공격 모델
2. LSB
3. 공개 행렬 *unpack*
4. 부호 비트
5. 샘플링 시드

---

<!-- _class: lead divider -->
# IV. 실험 설계 및 구현

1. 소프트웨어 오류 삽입
2. 하드웨어: *ChipWhisperer-Husky*, *STM32F4*
3. 실험 결과

---

<!-- _class: lead divider -->
# V. 대응 기법

1. 알고리즘 수준
2. 구현 수준
3. 성능 *overhead*

---

<!-- _class: lead divider -->
# VI. 결론
