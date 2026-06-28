# HAETAE 서명 알고리즘 상세 (KeyGen · Sign · Verify)

> 본 문서는 HAETAE **공식 레퍼런스 구현**(`src/sign.c`, `include/params.h`)을 근거로
> 키생성·서명·검증 알고리즘을 정리한 것입니다. 개요·파라미터는
> [`HAETAE_overview_ko.md`](HAETAE_overview_ko.md) 참조. 본 저장소의 결함주입 연구는
> 서명의 **응답 계산 단계(z = y + (-1)^b c·s)** 를 표적으로 합니다.

## 표기

- 환 $\mathcal{R}_q = \mathbb{Z}_q[x]/(x^{256}+1)$, $q=64513$, $N=256$.
- $\mathbf{A}_0 \in \mathcal{R}_q^{K\times M}$: 공개 행렬(시드에서 확장), $M=L-1$.
- $\mathbf{s}_1 \in \mathcal{R}^{M}$, $\mathbf{s}_2 \in \mathcal{R}^{K}$: 작은 비밀 벡터($\eta=1$).
- $\mathbf{b}$: 검증키 벡터(하위 $D$비트 절단). $\mathbf{y}=(\mathbf{y}_1,\mathbf{y}_2)$: 하이퍼볼 nonce.
- $c$: 챌린지($\pm1$, 해밍무게 $\tau$), $b\in\{0,1\}$: bimodal 부호.
- $L_N=8192$: 고정소수점 큰 스케일. $B_0,B_1$: 서명 경계, $B_2$: 검증 경계($B_1<B_2$).
- `round(·)`: 고정소수점 반올림, `HighBits/LowBits/LSB`: 비트 분해, `Hint`: 힌트.

---

## Algorithm 1 — KeyGen

```
입력: 없음 (난수)              출력: 공개키 vk, 비밀키 sk
1.  seed_A, sigma, key  <- 난수(엔트로피 rho)
2.  A0  <- ExpandA(seed_A)                         # 공개 행렬
3.  repeat                                         # 비밀키 노름 거부
4.      (s1, s2) <- ExpandS(sigma, counter++)      # 작은 비밀 (eta=1)
5.  until  sk_singular_value(s1, s2) 가 조건 만족
6.  b  <- A0 · s1 + s2  (mod q)                    # = 검증키 (NTT(-2b) 형태로 저장)
7.  vk <- pack(b, seed_A)
8.  sk <- pack(vk, s1, s2, key)
9.  return (vk, sk)
```

핵심: 공개키는 $\mathbf{b}=\mathbf{A}_0\mathbf{s}_1+\mathbf{s}_2$ 관계(MLWE)이며, 행렬
$\mathbf{A}_1=(-2\mathbf{b}+q\mathbf{j}\ \|\ 2\mathbf{A}_0)$ 형태로 검증에 쓰인다. 비밀키
$\mathbf{s}_1$이 본 연구의 복원 표적이다.

---

## Algorithm 2 — Sign  (FSwA + bimodal + hyperball)

```
입력: 메시지 M, 비밀키 sk = (s1, s2, ...)        출력: 서명 sigma = (c, z1, h)
1.  (A1, s1, s2, key) <- unpack(sk);  s1,s2 <- NTT(s1), NTT(s2)
2.  mu  <- H(pre || M)                              # 메시지 해시 (도메인분리 pre)
    (결정론적 경로: 시드는 key와 mu 결합으로 생성)

    repeat  (reject 루프):
3.  # ---- (1) 하이퍼볼에서 nonce 샘플링 ----
    (y1, y2, b) <- SampleHyperball(seedbuf, counter++)   # b: bimodal 부호 비트

4.  # ---- (2) 챌린지 c 계산 ----
    (zr1, zr2) <- round(y1), round(y2)
    Ay  <- A0·round(y1) + 2·round(y2)  (mod q)
    Ay  <- recover_mod_2q(Ay, round(y1)[0])            # fromCRT, freeze2q
    w   <- HighBits(Ay)                                 # 약속
    lsb <- LSB(round(y1)[0])                            # 홀짝 보정용
    c   <- Challenge( pack(w, lsb), mu )                # ±1, 무게 tau

5.  # ---- (3) 응답 z = y + (-1)^b · c·s ----   ★결함 표적★
    cs1[0] <- c ;  chat <- NTT(c)
    for i = 1 .. L-1:  cs1[i] <- InvNTT( chat ∘ s1[i-1] )   # c·s1   (T1: 스킵 시 z≈y)
    cs2     <- InvNTT( chat ∘ s2 )                          # c·s2
    cs1, cs2 <- cneg(cs1, b), cneg(cs2, b)                  # bimodal 부호
    z1 <- y1 + cs1 ;  z2 <- y2 + cs2                        # +y  (T2: 스킵 시 z1=Ln·c·s1)

6.  # ---- (4) 거부 샘플링 (서명 경계 B1, 보조 B0) ----
    if  ||(z1,z2)||^2  >=  B1^2 · Ln^2 :    reject  (-> 3)   # reject1
    if  b' 조건에서 ||2z - y||^2 < B0^2 :   reject  (-> 3)   # reject2 (bimodal)

7.  # ---- (5) 힌트·인코딩 ----
    (hb_z1, lb_z1) <- HighBits(round(z1)), LowBits(round(z1))
    h  <- MakeHint(z2, ...)                             # 검증 보정 힌트
    sigma <- encode(c, hb_z1, lb_z1, h)
8.  return sigma
```

**설계 요점.**
- **bimodal**(5단계 `cneg`): 부호 $b$로 $\pm c\mathbf{s}$를 선택해 거부율을 낮춘다.
- **하이퍼볼**(3단계): nonce를 이산 하이퍼볼 균등분포에서 추출 → 컴팩트 서명.
- **거부 샘플링**(6단계): **서명 경계 $B_1$**(및 bimodal용 $B_0$)을 사용. 검증 경계 $B_2$와
  다르다($B_1<B_2$). 이 차이가 본 저장소 대응기법(HAETAE-IRV)의 (M2) 근거이다.
- **결함 표적**: 5단계의 `c·s1`(T1)·`+y`(T2). T2 스킵 시 $\mathbf{z}_1=L_N\,c\,\mathbf{s}_1$
  → 공개 $c,L_N$으로 단일 트레이스 $\mathbf{s}_1$ 복원(저장소 README 참조).

---

## Algorithm 3 — Verify

```
입력: 서명 sigma, 메시지 M, 공개키 vk           출력: accept / reject
1.  A1 <- unpack(vk)                                # A1 = (-2b+qj || 2A0)
2.  (c, lowz, highz, h) <- unpack(sigma)            # 형식/조건 위반 시 reject
3.  z1 <- compose(highz, lowz)                      # 상·하위비트로 z1 복원
4.  w' <- z1[0] - c
    Ay' <- A1·round(z1) - q·c·j  (mod q -> 2q)
    w   <- HighBits(Ay', h)                         # 힌트로 보정
    z2' <- recover(w, w')                           # \tilde z2
5.  if  ||z1||^2 + ||z2'||^2  >  B2^2 :  reject     # ★검증 경계 B2★
6.  c' <- Challenge( pack(HighBits(Ay'), lsb), mu )
7.  if  c' != c :  reject
8.  return accept
```

**핵심(B₁ vs B₂).** 검증은 **느슨한 경계 $B_2$**(5단계)로 노름을 확인한다. 서명 생성은
**엄격한 $B_1$**(Alg 2의 6단계)을 쓴다. HAETAE-120 기준 $B_1=9838.98 < B_2=12777.52$.
따라서 거부 판정을 결함으로 우회해 노름이 $[B_1,B_2)$에 드는 응답은 **검증을 통과**하면서도
키 정보를 누설한다 → 단순 "서명 후 검증" 대응의 사각지대(저장소 §5.3/HAETAE-IRV가 해결).

---

## 결함주입 관점 요약

| 단계 | 표적 | 결함 효과 | 누설 |
|---|---|---|---|
| Sign 5 (`c·s1`) | T1 | $\mathbf{z}\approx\mathbf{y}$ | nonce |
| Sign 5 (`+y`) | **T2** | $\mathbf{z}_1=L_N c\,\mathbf{s}_1$ | **$\mathbf{s}_1$ 직접(단일 트레이스)** |
| Sign 6 (거부) | RB | 경계초과 $\mathbf{z}$ | 통계적 키정보 |
| Sign 3 (샘플링) | LA | 저엔트로피 $\mathbf{y}$ | nonce |

*근거: HAETAE 레퍼런스 `src/sign.c`(crypto_sign_signature_internal /
crypto_sign_keypair_internal / crypto_sign_verify_internal), `include/params.h`.*
