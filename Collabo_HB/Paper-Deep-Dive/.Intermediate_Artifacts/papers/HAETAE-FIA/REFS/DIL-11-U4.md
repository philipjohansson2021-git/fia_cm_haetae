# DIL-11-U4 — Verification-Bypass

단위: **DIL-11-U4**  
논문: [11] §6.2  
표준: FIPS 204 Algorithm 8 *Verify_internal*  
상태: **approved** (용어 수정 턴에서 슬라이드 반영) · presentation 반영

---

## 1. FI 대상

**출처:** [11] §6.2; 논문 simplified Verify L36 `ĉ = NTT(c)`.

| 층 | 위치 | 내용 |
|----|------|------|
| 논문 | Verify 의 $\mathrm{NTT}(c)$ | *twiddle* 전 zeroize |
| FIPS | Alg 8: $c\leftarrow\mathrm{SampleInBall}(\tilde{c})$ 후 $\mathrm{NTT}(c)$ (L8–9 계열) | 동일 대수 타겟 |

조건: $c_0=0$ → $\hat{c}^*=0$.

## 2. 오류 효과 (논문 Eq.16)

$$
w_1^* = \mathrm{UseHint}(h,\, A\cdot z)
\qquad
\text{(사실상 } \hat{c}^*=0 \text{ 일 때 } c\cdot t \text{ 항 소멸 계열)}
$$

$$
\tilde{c}^* \text{ 또는 } c^* = H(\mu \| w_1^*)
$$

$w_1^*$ 가 $(z,h)$ 만의 함수 → 공격자가 선택한 $(z^*,h^*)$ 로 맞춤.

## 3. 악성 서명 제작 (논문 Alg.4)

1. $(z^*,h^*)$ 를 규범 조건 만족하게 샘플
2. $w_1^* \leftarrow \mathrm{UseHint}(h^*, A z^*)$ (논문 표기; FIPS는 $t_1\cdot 2^d$ 등 포함 가능 — 이식 시 주의)
3. $c^*$ (또는 $\tilde{c}$) 유도, **$c_0^*=0$** 될 때까지 재시도
4. $\sigma^*=(z^*,h^*,c^*)$ (FIPS: $(\tilde{c},z,h)$ 인코딩)

## 4. 공격 실행

- Verify$(\sigma^*,\mu)$ 호출 중 $\mathrm{NTT}(c^*)$ fault  
- $\hat{c}^*=0$ → 재계산 *challenge* 가 악성 제작과 일치 → **accept**

논문: 1000 메시지 sim, **100%** (perfect fault 가정).

## 5. 비판·FIPS 이식

| 이슈 | 내용 |
|------|------|
| $\sigma$ 표기 | 논문 $(z,h,c)$ vs FIPS $(\tilde{c},z,h)$ — SampleInBall 리맵 |
| Alg.4 `while c0 = 0` | 본문 “until $c_0=0$” 과 **조건 표기 모순** 가능 (휴먼에러 후보). 의도는 $c_0\neq 0$ 인 동안 재시도 |
| UseHint / $A z$ | FIPS Verify 는 $Az - c t_1 2^d$ 후 UseHint — $\hat{c}=0$ 이면 $Az$ 쪽 단순화. 세부 이식은 Alg 8 대조 필요 |
| 구현 | *twiddle-pointer* FI 성공 여부 구현 의존 |

**요지:** *challenge NTT* 붕괴로 검증식을 공격자 통제 가능 — **적응 후 요지 유지 가능**.

## 6. 슬라이드 요지 (승인 후)

1. 타겟 Verify $\mathrm{NTT}(c)$ · $c_0=0$  
2. $w_1^*$ · 악성 $\sigma^*$  
3. 공격 단계 · 한계·FIPS 표기  
