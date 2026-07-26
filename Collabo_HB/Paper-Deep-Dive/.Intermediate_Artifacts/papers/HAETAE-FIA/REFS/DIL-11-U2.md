# DIL-11-U2 — Attack-1 `Sign_Fault_NTT_C` (FIPS 204 기준)

단위: **DIL-11-U2**  
논문: [11] §6.1.1 *Sign_Fault_NTT_C*  
표준: FIPS 204 **Algorithm 7** (특히 L15–20), **Algorithm 2** (deterministic $rnd$), **Algorithm 29** *SampleInBall*, **Algorithm 41**  
상태: **approved** (`작업 계속`) · presentation 반영

용어 정책 (D26): 전문 용어 *English italic*, 일상 설명 한글.

---

## 1. FI 대상 라인 (표준)

| 층 | 위치 | 내용 |
|----|------|------|
| 상위 | Alg 7 **L17** | $\hat{c}\leftarrow\mathrm{NTT}(c)$ |
| 하위 | Alg 41 **L10** | $z\leftarrow\texttt{zetas}[m]$ — *twiddle* 로드 |
| 오류 가정 | 구현 | 이 NTT 호출에서 **전** *twiddle* $z=0$ (U1 대수 모델) |

선행 조건 (논문 + FIPS 이식):

1. **Deterministic** *signing*: Alg 2에서 $rnd\leftarrow\{0\}^{32}$ (또는 동일 $rnd$ 고정)  
   → 동일 메시지 $M'$ 재서명 시, 동일 $\kappa$면 **동일** $y=\mathrm{ExpandMask}(\rho'',\kappa)$
2. 메시지(또는 시도)를 골라 *challenge* $c=\mathrm{SampleInBall}(\tilde{c})$ 의 **첫 계수** $c_0=0$

---

## 2. 정상 경로 (FIPS Alg 7, 해당 줄만)

```
15:  c̃ ← H(μ || w1Encode(w1), λ/4)
16:  c  ← SampleInBall(c̃)
17:  ĉ  ← NTT(c)
18:  ⟨⟨c s1⟩⟩ ← NTT^{-1}(ĉ ∘ ŝ1)
20:  z  ← y + ⟨⟨c s1⟩⟩
```

대수적으로 (단일 다항식으로 단순화, 논문과 동일; 벡터는 성분별):

$$
z \;=\; y + c\cdot s_1
$$

($c\cdot s_1$ 은 실제로는 *NTT domain* *pointwise multiplication* 후 $\mathrm{NTT}^{-1}$).

공개 정보: 서명 $\sigma$의 $\tilde{c}$ → $c=\mathrm{SampleInBall}(\tilde{c})$ (FIPS; 논문이 “$c$가 서명에 있다”고 한 부분의 **리맵**).

---

## 3. 오류가 값을 바꾸는 방식

대상: L17 $\mathrm{NTT}(c)$, 입력 $c=(c_0,c_1,\ldots,c_{255})$, **$c_0=0$**.

| | 정상 $\hat{c}$ | 오류 $\hat{c}^*$ (전 *twiddle* $=0$) |
|--|----------------|--------------------------------------|
| 정의 | Alg 41 정상 출력 | $\hat{c}^*[i]=c_0=0$ $\forall i$ |
| 의미 | 일반 *challenge* *NTT* | **영벡터** $\hat{c}^*=0$ |

이어서 L18–20:

$$
\langle\langle c s_1\rangle\rangle^*
=\mathrm{NTT}^{-1}(\hat{c}^*\circ\hat{s}_1)
=\mathrm{NTT}^{-1}(0)
=0
$$

$$
z^* \;=\; y + 0 \;=\; y
$$

논문 Eq.(13)과 **동일한 귀결** (FIPS 기본 $z$ 경로와 정합).

---

## 4. 알고리즘을 따른 전파 · 출력

| 단계 | 정상 실행 | 오류 실행 (동일 $m$, 동일 $\kappa$) |
|------|-----------|-------------------------------------|
| $y$ | $\mathrm{ExpandMask}(\rho'',\kappa)$ | **동일** $y$ (det + 동일 $\kappa$) |
| $w,w_1,\tilde{c},c$ | 정상 | **동일** ($c$는 $w_1$에서 유도; NTT fault는 **그 이후**) |
| $\hat{c}$ | 정상 | $\hat{c}^*=0$ |
| $z$ | $y+c s_1$ | $z^*=y$ |
| 이후 rejection / $h$ | 통과 가능 | 오류 중간값으로 **다른** rejection 가능 |

서명 출력:

- 정상: $(\tilde{c},\,z,\,h)$ (유효 가능)
- 오류: $(\tilde{c},\,z^*,\,h^*)$ — 논문: **invalid** 인 경우가 많음  
  ($z^*=y$ 이지만 검증은 $\mathbf{A}z-c t_1 2^d$ 등과 불일치)

---

## 5. 비밀키 복구

동일 $\kappa$가 보장될 때:

$$
\Delta z \;=\; z - z^* \;=\; (y + c s_1) - y \;=\; c\cdot s_1
$$

$c$ public ⇒

$$
s_1 \;=\; (\Delta z)\cdot c^{-1} \quad \text{in } R_q
$$

(성분 다항식마다; 모듈 $\mathbf{s}_1\in R_q^\ell$ 로 확장 — 논문: 성분 독립 처리.)

### 성공 조건 · 논문 수치

| 조건 | 내용 | 비판 |
|------|------|------|
| $\Delta\kappa=0$ | 정상·오류 모두 같은 *rejection* 횟수 | 오류 시 L23 등 검사가 달라져 **실패 가능** — 논문 인정 |
| $c_0=0$ | *SampleInBall* 후 | FIPS에서도 탐색 가능; $P(c_0\neq0)\approx\tau/256$ |
| $c$ invertible | $\Delta z\cdot c^{-1}$ | sparse $c$가 항상 unit **아님** → 실패 시 다른 샘플 (논문은 “easily” — **다소 낙관**) |
| 필요 서명 수 | 시뮬레이션 평균 **≈13**, 1000키, **perfect fault** 가정 | **구현 FI 성공률과 별개** |
| 모드 | **deterministic only** | probabilistic에는 **차분** 불가 (논문 명시) |

*Countermeasure* (논문): *Verify_After_Sign* — 오류 서명이 invalid면 탐지 용이.

---

## 6. 논문 주장 vs FIPS — 비판적 점검

| 논문 서술 | FIPS 대응 | 판정 |
|-----------|-----------|------|
| $z=\mathrm{INTT}(\hat{s}_1\circ\hat{c})+y$ | Alg 7 L18+L20 | **일치** |
| $\sigma=(z,h,c)$ | $(\tilde{c},z,h)$ | 표기만; $c$ 복원 가능 |
| fault → $c^*=(c_0,0,\ldots)$ with $c_0=0$ ⇒ 0 | Alg 41 $z=0$ 모델 | **대수 일치** |
| $s=\Delta z\cdot c^{-1}$ | 동일 | **가역성** 주의 |
| ≈13 signatures, 100% | perfect fault sim | **실측 EMFI 성공률 ≠ 이 숫자** |
| det only | Alg 2 $rnd=\{0\}^{32}$ | **일치** |

**한 줄:** Attack-1 요지는 FIPS 204 기본 *Sign* 위에서 **구조적으로 성립**.  
한계는 (1) det 모드 (2) 동일 $\kappa$ (3) $c^{-1}$ (4) **구현상** *twiddle* 전 zeroize 가능 여부.

---

## 7. C 코드

- 로컬 pqm4 없음
- 논문: *NTT* of $c$ 직전 *twiddle-pointer* load 가 타겟 (asm 스케치 U1)
- 사용자 경로 제공 시 `poly_ntt` / challenge 경로 라인 매핑

---

## 8. 슬라이드 요지 (승인 후)

1. 타겟: Alg 7 L17 + Alg 41  
2. 정상 $z=y+c s_1$ / 오류 $z^*=y$  
3. $\Delta z=c s_1$ → $s_1$  
4. 조건·한계 표 (det, $\kappa$, 구현, *Verify_After_Sign*)
