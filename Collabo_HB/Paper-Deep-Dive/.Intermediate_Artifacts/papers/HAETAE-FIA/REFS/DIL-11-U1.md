# DIL-11-U1 — NTT Twiddle Zeroization Fault Model ↔ FIPS 204

단위: **DIL-11-U1** (개정: 답변 칸 피드백 반영)  
논문: [11] Ravi et al., TCHES 2023 No.2  
표준: FIPS 204 **Algorithm 41 NTT**, **Algorithm 7/8**  
상태: **approved** (D29) · presentation 반영 (Alg 41 전문, 수정 없음)

피드백 반영:
1. **FIPS Alg 41 전체 간략 설명**을 선행
2. **논문↔표준 불일치**가 공격 추적에 미치는 영향 · 구조적 불가능 vs 마이너 수정

---

## A. FIPS 204 Algorithm 41 NTT — 전체 간략 설명 (1슬라이드분)

### 역할

- 입력: 다항식 $w\in R_q=\mathbb{Z}_q[X]/(X^{256}+1)$ (계수 256개)
- 출력: NTT 영역 튜플 $\hat{w}\in T_q$ (역시 길이 256)
- 목적: 다항식 곱 $a\cdot b$ 를  
  $\mathrm{NTT}^{-1}\big(\mathrm{NTT}(a)\circ\mathrm{NTT}(b)\big)$  
  로 바꿔 **점별곱**으로 가속 (Sign/Verify·KeyGen 공통 커널)

### 구조 (표준 의사코드 요약)

| 구간 | 라인 | 하는 일 |
|------|------|---------|
| 초기화 | 1–3 | 계수 배열 $\hat{w}[j]\leftarrow w_j$ 복사 |
| 루프 설정 | 4–5 | $m\leftarrow 0$, $\mathrm{len}\leftarrow 128$ |
| 외곽 while | 6–19 | $\mathrm{len}=128,64,\ldots,1$ — **8 stages** (complete NTT) |
| 내곽 while | 8–17 | 각 stage의 butterfly 블록 |
| twiddle | **10** | $z\leftarrow\texttt{zetas}[m]$ — 사전계산 $512$제곱근 거듭제곱 |
| butterfly | 12–14 | $t\leftarrow(z\cdot\hat{w}[j+\mathrm{len}])\bmod q$  
  후 $\hat{w}[j+\mathrm{len}]\leftarrow\hat{w}[j]-t$, $\hat{w}[j]\leftarrow\hat{w}[j]+t$ (CT형) |
| 반환 | 20 | $\hat{w}$ |

표준이 명시한 상수:

- $\zeta=1753\in\mathbb{Z}_q$ (512th root of unity, §2.5)
- $\texttt{zetas}[1..255]$ = Appendix B 표 (Montgomery form 저장 가능)
- 수학적 의미 (Eq 7.1): $\mathrm{NTT}(w)=\big(w(\zeta_0),\ldots,w(\zeta_{255})\big)$

**한 줄:** Alg 41은 “고정 테이블 `zetas`를 쓰는 **완전(complete) 8-stage CT-NTT**”이다.  
오류 모델이 건드리는 지점은 본질적으로 **line 10의 $z$**.

### $z=0$ 일 때의 대수적 귀결 (표준만으로 검증 가능)

$$
t=0 \;\Rightarrow\; \hat{w}[j+\mathrm{len}]=\hat{w}[j],\;\hat{w}[j]=\hat{w}[j]
$$

전 stage·전 twiddle이 0이면 출력은 **입력 첫 계수 $w_0$ 의 256회 반복**.  
→ 논문 “entropy collapse”의 **수학 핵은 FIPS와 정합**.

### 표준이 말하지 않는 것

- `zetas`를 **포인터 $T$로 flash load** 하는 방식 → 구현
- 단일 EMFI로 $T$를 zero 영역으로 돌리는 것 → 구현·보드
- 동일 모듈 연속 NTT에 fault 전파 → 캐시 가설 (논문 §7)

---

## B. 논문 오류 모델 (§4) — Alg 41 이후 설명

(이전 U1 §1과 동일 요지)

1. CT butterfly에서 $w=0$ → $(x_0,x_0)$
2. **Twiddle-pointer vulnerability** (pqm4 M4): 한 번의 pointer 오류로 전 twiddle 0
3. Dilithium complete NTT ($n=256$) — Kyber incomplete와 구분
4. 실험: 모듈 내 다수 NTT에 단일 fault 전파 (표준 속성 아님)

---

## C. Sign/Verify에서의 NTT 호출점 (FIPS)

### Algorithm 7 Sign_internal

| L# | 호출 | 비고 |
|----|------|------|
| 2–4 | $\mathrm{NTT}(s_1),\,\mathrm{NTT}(s_2),\,\mathrm{NTT}(t_0)$ | 루프 밖 |
| 12 | $\mathrm{NTT}^{-1}(\hat{A}\circ\mathrm{NTT}(y))$ | 매 루프: **NTT(y)** 포함 |
| 17 | $\hat{c}\leftarrow\mathrm{NTT}(c)$ | 매 루프: **challenge** |
| 18–19, 25 | 관련 INTT | $cs_1,cs_2,ct_0$ |

### Algorithm 8 Verify_internal

| L# | 호출 |
|----|------|
| 9 | $\mathrm{NTT}(z)$, $\mathrm{NTT}(c)$, $\mathrm{NTT}(t_1\cdot 2^d)$ + INTT |

---

## D. 논문↔표준 대응표

| 논문 Alg.2 (simplified) | FIPS 204 | 대응 성격 |
|-------------------------|----------|-----------|
| L19 SampleY | L11 ExpandMask | 역할 동일, 이름·시드 상이 |
| L20 NTT(y) | L12 **내부** | 분리 줄 여부만 다름 |
| L21 w, w1 | L12–13 | 대응 |
| L22 $c\leftarrow H(\mu\|w_1)$ | L15–16 $\tilde{c}\leftarrow H$; $c\leftarrow\mathrm{SampleInBall}(\tilde{c})$ | **표기 축약** |
| L23 NTT(c) | L17 | 대응 |
| L24 $z=\mathrm{INTT}(\hat{c}\circ\hat{s}_1)+y$ | L18+L20 | **기본 경로 동일** |
| $\sigma=(z,h,c)$ | $\sigma=(\tilde{c},z,h)$ | **서명 필드 표기** |
| (대안) $z=\mathrm{INTT}(\hat{s}_1\circ\hat{c}+\hat{y})$ | **표준에 없음** | 구현 선택 |

---

## E. 불일치가 공격 추적에 미치는 영향 (핵심 논의)

### E.1 서명 구성: $(z,h,c)$ vs $(\tilde{c},z,h)$

| 질문 | 판단 |
|------|------|
| 무엇을 모르는가? | 논문은 challenge **다항식** $c$가 서명에 실린다고 씀. FIPS는 **해시 바이트** $\tilde{c}$만 실음. |
| 공격자가 $c$를 알 수 있는가? | **예.** 공개 서명에서 $\tilde{c}$를 읽고 로컬로 $c\leftarrow\mathrm{SampleInBall}(\tilde{c})$ (Alg 29). 검증자도 동일. |
| 공격 논리 영향 | **표기 리맵만.** “$c$를 안다 → $s_1$ 역산” 류 논리는 **유지**. |

**판정:** 구조적 불가능 **아님**. 마이너 수정(항상 $\tilde{c}\mapsto c$).

### E.2 challenge 생성: $H$ 직결 vs SampleInBall

| 질문 | 판단 |
|------|------|
| 논문 simplified | $c$를 해시 출력처럼 취급 (과도 단순화) |
| FIPS | $\tilde{c}$는 해시, $c$는 $\tau$개의 $\pm1$ sparse (Alg 29) |
| “$c_0=0$인 메시지 선택” | SampleInBall 후 $c_0=0$이 될 때까지 메시지/난수 재시도. $c_0\neq0$ 확률 $\approx\tau/256$ (대략 15–23%) → $c_0=0$이 **대다수**. 논문 조건은 **더 쉬워질 수 있음**. |
| 영향 | 탐색 대상이 “해시 비트”가 아니라 **SampleInBall 출력 계수**. 절차만 명시하면 됨. |

**판정:** 구조적 불가능 **아님**. 마이너 수정(조건 검사 위치를 SampleInBall 이후로).

### E.3 라인 번호·함수명 불일치

- 논문 L20/L23/L24 ≠ FIPS L12/L17/L20  
- **가독성·트리거 타이밍 설명**에만 영향. 대수 논리 불변.

**판정:** 마이너 (대응표로 해소).

### E.4 $z$ 계산 경로 — Attack-2에 결정적

| 경로 | FIPS Alg 7 | 논문 Attack-2 가정 |
|------|------------|-------------------|
| 기본 | $z\leftarrow y+\mathrm{NTT}^{-1}(\hat{c}\circ\hat{s}_1)$  (**$y$ normal domain 가산**, L20) | — |
| 대안 | **표준 의사코드에 없음** | $z\leftarrow\mathrm{NTT}^{-1}(\hat{s}_1\circ\hat{c}+\hat{y})$ |

논문 스스로: *“We are not aware of a public implementation of Dilithium adopting this approach.”*  
대안은 Skip_Add 방어·메모리 절약 **동기**로만 제시.

**Attack-2 (`Sign_Fault_NTT_Y`) 영향:**

- 오류 NTT($y$)가 $z$에 저엔트로피로 직접 스며드는 식 (논문 Eq.14–15) 은 **대안 경로 전제**
- **FIPS 기본 구현**에서는 NTT($y$)는 주로 $\mathbf{w}=\mathbf{A}\mathbf{y}$ (L12)에 쓰이고, $z$는 **정상 $y$** 를 더함  
  → 논문 Eq.15 형태의 “$z^*$ 계수 대부분이 $sc$” **그대로는 성립하지 않음**
- 따라서 Attack-2는 “표준 ML-DSA 필수 경로의 필연적 취약점”이 **아님**.  
  **특정 구현 선택 하의 조건부 공격**.

**판정:**  
- **표준 기본 Sign에 대해 Attack-2 as written → 구조적으로 적용 불가(또는 전면 재분석 필요)**  
- 논문 요지 전체(“NTT twiddle fault로 Dilithium 위협”)까지 무너지진 않음 — **Attack-1·Verify-Bypass는 다른 경로**

### E.5 Attack-1 (`Sign_Fault_NTT_C`) — FIPS에 이식

목표: $\mathrm{NTT}(c)$ (FIPS L17) twiddle 전 zeroize.

논문 (det, 동일 $m$, 동일 $\kappa$ 가정):

1. 정상: $z = y + c\cdot s_1$
2. $c_0=0$ + fault NTT($c$) → 실효 $c^*=0$ → $z^*=y$
3. $\Delta z = z-z^* = c\cdot s_1$ → $s_1=\Delta z\cdot c^{-1}$

FIPS 이식:

1. $c\leftarrow\mathrm{SampleInBall}(\tilde{c})$ 로 공개 $c$ 확보 — **OK**
2. $c_0=0$ 탐색 — **OK** (E.2)
3. $z=y+\langle\langle cs_1\rangle\rangle$ 구조 **FIPS L18–20과 동일** — **OK**
4. det 모드: $rnd=\{0\}^{32}$ (Alg 2 L5 주석) — 동일 메시지 재서명 시 $y$ 재현 가능 **전제 유지**
5. rejection $\kappa$ 정합 — 논문이 이미 인정한 **성공률 제한** (≈13 sig), FIPS와 무관
6. ⚠ $c^{-1}$ 존재: $R_q$에서 sparse $c$가 항상 unit은 **아님**. 논문은 “easily”라고 하나, **역원 없는 $c$면 해당 샘플 폐기·재시도**가 필요 — **마이너 운영 이슈**, 공격 클래스 파괴는 아님 (많은 $c$는 NTT 영역 0계수 없으면 가역)

**판정:** **공격 논리 생존. 마이너 수정으로 요지 유지.**  
(구현 FI 가능 여부는 별개 실험 문제)

### E.6 Verification-Bypass

논문: Verify에서 NTT($c$) fault, $c_0=0$이면 $\hat{c}^*=0$ → $w_1'$가 $(z,h)$만의 함수 → 악성 $\sigma$ 제작.

FIPS Alg 8:

- $\tilde{c}$ 디코드 → $c\leftarrow\mathrm{SampleInBall}(\tilde{c})$ → $\mathrm{NTT}(c)$ 사용 (L8–9)
- 서명 필드는 $\tilde{c}$ — 악성 서명도 $\tilde{c}$를 심고 SampleInBall 결과가 $c_0=0$이 되게 설계

**판정:** 표기·인코딩 적응 필요하나 **핵심 아이디어( challenge NTT 붕괴 → 검증식 공격자 통제 )는 유지 가능**. 구조적 불가능 **아님**.  
(논문 Alg.4 `while c0=0` 표기는 서술과 모순 가능 — 휴먼에러 후보, U4에서 재검토)

### E.7 Twiddle-pointer 단일 fault

- Alg 41 **수학**과 무관하게 **구현 전제**
- FIPS 준수 구현이 on-the-fly zetas / integrity check를 쓰면 **논문 실험 조건 붕괴** 가능
- 이건 “표준 불일치”가 아니라 “**구현 다양성**” 문제

**판정:** 표준만으로 공격 성공을 **보장하지 않음**. 그러나 “표준 알고리즘이 공격을 수학적으로 봉쇄”하지도 않음.

---

## F. 종합 판정표 (사용자 질문 직답)

| 불일치 포인트 | 구조적으로 공격 불가능? | 마이너 수정으로 논문 요지 유지? |
|---------------|------------------------|--------------------------------|
| $\sigma$에 $c$ vs $\tilde{c}$ | **아니오** | **예** — SampleInBall 리맵 |
| $H$ vs SampleInBall | **아니오** | **예** — $c_0$ 검사 위치 |
| 라인/함수명 | **아니오** | **예** — 대응표 |
| **$z$ 대안 경로 (Attack-2)** | **기본 FIPS 경로에서는 as-written 불가** | **Attack-2 요지만 조건부**; 논문 전체 요지는 Attack-1 등으로 부분 유지 |
| FI로 전 twiddle=0 | 표준이 금지/강제 안 함 | 구현 의존; 대수 핵은 유지 |
| **Attack-1 전체** | **아니오** | **예** (det·$\kappa$·$c^{-1}$ 운영 조건) |
| **Verify-Bypass** | **아니오** (현재 분석) | **예** (인코딩 적응) |

### 한 줄 결론

> **[11]의 NTT-twiddle 오류 모델과 Attack-1·(적응된) Verify-Bypass 요지는 FIPS 204 위에서도 살아 있다.**  
> 불일치는 대부분 **표기·SampleInBall·서명 필드** 수준의 마이너 수정으로 흡수된다.  
> **예외적으로 Attack-2는 FIPS 기본 $z$ 계산을 따르지 않는 구현을 전제**하므로, “표준 ML-DSA 기본 서명 = 그대로 깨짐”으로 읽으면 **과대 해석**이다.

---

## G. C 코드

- 로컬 pqm4 없음 → 이전과 동일
- 경로 제공 시 Alg 41 L10 ↔ load twiddle-ptr 매핑 보강

---

## H. 다음 단위

**DIL-11-U2:** Attack-1 전개 (FIPS L17 기준 수식·$\Delta z$·$\kappa$·$c^{-1}$·필요 서명 수·비판)
