# DIL-09-U1 — ExpandMask · nonce++ skip 오류 모델

단위: **DIL-09-U1**  
논문: [9] ElGhamrawy et al., TCHES 2023 No.4, §3  
표준: FIPS 204 **Algorithm 34 ExpandMask**, **Algorithm 7** L11  
상태: **approved** (`승인`) · presentation 반영 (Alg 34 + skip + 수치 예)

---

## 1. FI 대상 (논문)

**출처:** [9] §3, Fig.1 (asm/C listing)

- 함수: `polyvecl_uniform_gamma1` / *ExpandMask* 대응
- 각 성분: $y[i] \leftarrow \mathrm{ExpandMask}(\rho',\, \kappa\cdot\ell + i)$
- **Fault:** 루프 내 **nonce 증가 명령 *instruction skip***
- **효과:** 연속 두 성분에 **동일 nonce** → $y[i]=y[j]$ (예: $y[0]=y[1]$)

## 2. FIPS 204 Algorithm 34 ExpandMask (수정 없이 수록 예정)

```
Algorithm 34 ExpandMask(ρ, μ)
 1: c ← 1 + bitlen(γ1 − 1)
 2: for r from 0 to ℓ − 1 do
 3:     ρ' ← ρ || IntegerToBytes(μ + r, 2)
 4:     v ← H(ρ', 32c)
 5:     y[r] ← BitUnpack(v, γ1 − 1, γ1)
 6: end for
 7: return y
```

Sign_internal L11: $\mathbf{y}\leftarrow\mathrm{ExpandMask}(\rho'',\kappa)$  
→ 구현이 $r=0..\ell-1$ 에 $\mu+r$ 를 쓰면, **$\mu+r$ 증가 skip** 이 논문 fault 와 대응.

## 3. 오류가 값에 미치는 영향

정상: $y[r]$ 는 $\mu+r$ 마다 독립 샘플.  
오류 (예: $r=1$ 에서 증가 skip): $\mu$ 동일 → $y[0]=y[1]$ (동일 시드 확장).

## 4. 다음 단위 (U2)

$z=y+c s_1$ 에서 $\Delta z = z[i]-z[j] = c(s_1[i]-s_1[j])$ → MLWE→RLWE.

## 5. 비판 메모

| 항목 | 내용 |
|------|------|
| 실증 | [9] 는 skip **실측 없음** (모델·sim; 타 문헌 인용) |
| FIPS | ExpandMask 의사코드는 $\mu+r$ 증가를 명시 — skip 대상은 **구현 루프** |
| 서명 모드 | det + rand (rand는 주로 첫 시도 fault 전략) |
