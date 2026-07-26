# 팩트체크 — [11] “$c$가 sparse이므로 NTT를 굳이 적용하지 않을 것”

요청: 동료 피드백  
> “[11]에서 $c$는 sparse한 값이라 NTT를 굳이 적용하지 않을 것 같다”

판정 일: 2026-07-23  
근거: 로컬 PDF [11], FIPS 204 (표준문서), 기존 DIL-11-U1/U2

---

## 1. 한 줄 결론

| 주장 조각 | 판정 |
|-----------|------|
| $c$가 **sparse** 다항식이다 | **사실** ([11], FIPS SampleInBall) |
| 그래서 **NTT($c$)를 하지 않는다 / 하지 않을 것이다** | **사실 아님** (표준·[11] 의사코드·EMFI 실험 모두 NTT($c$) 전제) |
| sparse이면 NTT 없이도 $c\cdot s_1$ 계산이 **수학적으로 가능**하다 | **가능** (대안 구현). 다만 표준·대상 구현의 기본 경로가 아님 |
| Attack-1(`Sign_Fault_NTT_C`) 타겟이 성립하려면 | **구현이 NTT($c$)를 수행**해야 함 → [11]이 pqm4 계열에서 실제로 주입·성공 보고 |

**종합:** 전제(sparse)는 맞고, **“그래서 NTT를 안 쓴다”는 추론은 [11]·FIPS·실험과 모순**.  
동료 의견은 “최적화 구현이 sparse 곱을 쓸 수도 있지 않나?”라는 **합리적 의심**으로 읽을 수 있으나, **[11]이 분석·실증한 대상에서는 NTT($c$)를 사용**한다.

---

## 2. $c$가 sparse인가? — **예**

### [11] (논문 본문)

- Alg.2 L22 주석: *“Generate Sparse Challenge $c$”*
- §본문: $c\in R_q$, 계수 약 60개가 $\pm1$, 나머지 0 (파라미터에 따라 $\tau$; Dilithium3 맥락)
- Attack-1 §6.1.1: *“challenge polynomial $c$ is sparse with coefficients in $\{-1,0,1\}$”*

### FIPS 204

- Alg 7 L16: $c\leftarrow\mathrm{SampleInBall}(\tilde{c})$
- 설명 문단: $c$의 계수는 $\{-1,0,1\}$, Hamming weight $\tau$

→ **“sparse” 자체는 동료·논문·표준이 일치.**

---

## 3. 그래도 NTT($c$)를 하는가? — **예 (표준·논문·실험)**

### 3.1 [11] 의사코드 (Alg.2)

| 줄 | 내용 |
|----|------|
| 22 | sparse challenge $c$ 생성 |
| **23** | $\hat{c}=\mathrm{NTT}(c)$ |
| 24 | $z=\mathrm{INTT}(\hat{c}\circ\hat{s}_1)+y$ |

논문은 sparse임을 **상기시킨 직후**에도 NTT($c$)를 **명시적으로** 둔다.  
“sparse이므로 NTT 생략” 서술은 **없음**.

### 3.2 FIPS 204 Algorithm 7 (Sign_internal)

| 줄 | 내용 |
|----|------|
| 16 | $c\leftarrow\mathrm{SampleInBall}(\tilde{c})$ |
| **17** | $\hat{c}\leftarrow\mathrm{NTT}(c)$ |
| 18 | $\langle\langle c s_1\rangle\rangle\leftarrow\mathrm{NTT}^{-1}(\hat{c}\circ\hat{s}_1)$ |
| 19–25 | 동일 $\hat{c}$로 $cs_2$, $ct_0$ 등 |

표준 기본 경로는 **NTT 기반 스칼라-벡터 곱**이며, sparse schoolbook 곱으로 대체하라고 **하지 않음**.

### 3.3 [11] 실험 (§7.3.3)

- *“fault the **NTT of the challenge polynomial $c$** in the signing procedure”*
- 10 100회 주입, 성공 fault ≈51%, 키 복구 테스트 100% (조건 하)
- 대상: pqm4 계열 ARM Cortex-M4 구현

→ 실험 대상 구현에서 **NTT($c$) 코드 경로가 실제로 존재**하고, 그 구간에 EMFI가 들어감.  
“구현이 NTT($c$)를 안 한다”면 이 절의 실험 서술이 성립하지 않음.

### 3.4 Verify 경로

- [11] Verify L36: $\hat{c}=\mathrm{NTT}(c)$
- Verification-Bypass도 **challenge NTT**를 타겟
- FIPS Alg 8도 $c$ 복원 후 NTT 사용 (동일 계열)

---

## 4. 동료 추론이 생기는 지점 (부분 타당)

| 관찰 | 해석 |
|------|------|
| $c$는 weight $\tau\ll n$ | normal domain에서 $c\cdot s_1$은 **$\tau$개 항의 shift-add**로도 계산 가능 (이론상) |
| NTT($c$)는 dense 길이 $n$ 변환 | 연산량 관점에서 “sparse면 NTT가 비효율” 직관이 생김 |
| 그러나 | (1) **FIPS 의사코드가 NTT 경로를 지정** (2) 구현은 **통일된 NTT 커널·상수시간·코드 단순성**을 위해 흔히 NTT($c$) 유지 (3) [11] 대상·실험이 그 경로 |

**대안 구현이 불가능한가?**  
- 불가능하지는 않음. 다만 그건 **다른 구현 선택**.  
- [11] Attack-1의 전제는 **“해당 구현이 NTT($c$)를 수행한다”** 이며, 논문은 그 전제를 실험으로 뒷받침.

**Attack-1이 “모든 가능 구현”을 깨나?**  
- 아니요. **NTT($c$)를 쓰는 구현** (표준 경로·pqm4류)에 대한 공격.  
- sparse-mult only 구현에는 **같은 타겟이 없음** → 동료 의견은 “대응/구현 다양성” 논의로는 유효, “논문이 틀렸다”는 팩트로는 **과대**.

---

## 5. 발표자료 관점 (D32·비판적 검증)

| 현재 deep-dive 서술 | 팩트체크 후 |
|---------------------|-------------|
| Attack-1 타겟 = Alg 7 L17 NTT($c$) | **유지** |
| $c$ sparse + $c_0=0$ 조건 | **유지** (논문 원문과 일치) |
| “구현은 반드시 NTT($c$)”를 전 세계 모든 코드에 일반화 | **과하면 안 됨** — “FIPS·[11] 대상 구현 경로”로 한정 권장 |
| 동료 오해 방지 슬라이드 | 선택: “sparse ≠ NTT 생략” 1장 추가 가능 (사용자 승인 후) |

---

## 6. 인용 앵커 (원문 요지)

1. [11] Alg.2 L22–24: Sparse Challenge → **NTT($c$)** → $z=\mathrm{INTT}(\hat{c}\circ\hat{s}_1)+y$  
2. [11] §6.1.1: 타겟 = **NTT of $c$**; sparse 상기 후 fault → $c^*\!=0$ (with $c_0=0$)  
3. [11] §7.3.3: EMFI on **NTT of $c$** in deterministic signing  
4. FIPS 204 Alg 7 L16–18: SampleInBall → **NTT($c$)** → $\mathrm{NTT}^{-1}(\hat{c}\circ\hat{s}_1)$

---

## 7. 사용자에게 제시할 문장 (To_Do용)

> 동료 말씀 중 **“$c$는 sparse”는 맞습니다.**  
> 그러나 [11]과 FIPS 204는 sparse $c$에 대해 **여전히 $\mathrm{NTT}(c)$를 수행**하고, $c\cdot s_1$을 NTT 영역 점별곱으로 계산합니다.  
> [11]은 그 NTT($c$)에 실제로 EMFI를 넣어 Attack-1을 실증했습니다.  
> “sparse이니 NTT를 안 할 것”은 **대안 구현 가설**로는 가능하나, **[11]·표준·대상 구현의 사실과 맞지 않습니다.**
