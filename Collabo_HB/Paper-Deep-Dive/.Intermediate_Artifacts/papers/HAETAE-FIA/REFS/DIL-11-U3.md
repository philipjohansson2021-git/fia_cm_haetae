# DIL-11-U3 — Attack-2 `Sign_Fault_NTT_Y` (조건부)

단위: **DIL-11-U3**  
논문: [11] §6.1.2 *Sign_Fault_NTT_Y*  
표준: FIPS 204 Algorithm 7 (기본 $z$ 경로)  
상태: **approved** (`승인`) · presentation 반영

---

## 1. 논문이 가정하는 구현 (존재 자료)

**출처:** [11] §6.1.2

- 기본(공개 pqm4 등): $z \leftarrow y + \mathrm{INTT}(\hat{c}\circ\hat{s}_1)$  (normal-domain $y$ 가산)  
  → FIPS Alg 7 L18+L20 과 동일
- **대안 구현** (논문 제안·Skip_Add 대응·메모리 절약):  
  $$
  z = \mathrm{INTT}(\hat{s}_1\circ\hat{c}+\hat{y})
  $$
- 논문: *“We are not aware of a public implementation … adopting this approach.”*

## 2. FI 대상

- $\mathrm{NTT}(y)$ (논문 Alg.2 L20 / FIPS L12 내부)
- 전 *twiddle* 0 → $\hat{y}^*$ 저엔트로피 (첫 계수 반복)
- 대안 $z$ 경로에서만 $z^*$ 계수 대부분이 $c s_1$ 로 노출 (논문 Eq.15)

## 3. FIPS 기본 경로 비판

- FIPS L20 은 $y$ 를 normal domain 에서 더함  
- $\mathrm{NTT}(y)$ fault 는 주로 $\mathbf{w}=\mathbf{A}\mathbf{y}$ 에 영향  
- 논문 Eq.14–15 **as-written 은 기본 FIPS 구현에 비적용**

## 4. 슬라이드 요지 (승인 후)

1. 대안 $z$ 식 vs FIPS L20  
2. 오류 시 $z^*$ 형태 (논문)  
3. 키 복구·≈3 sig (sim)  
4. **조건부** 한계 명시 (과대 해석 금지)
