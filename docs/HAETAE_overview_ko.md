# HAETAE 알고리즘 설명서 (KpqC 격자 기반 전자서명)

> 본 문서는 본 저장소의 결함주입 연구(HAETAE-IRV)를 이해하기 위한 HAETAE 알고리즘
> 요약 설명서입니다. 파라미터 수치는 HAETAE **공식 레퍼런스 구현**의 `params.h`에서
> 직접 확인한 값입니다. 자세한 정의·증명은 공식 명세를 참조하세요.

## 1. 개요

**HAETAE** (Hyperball bimodAl modulE rejecTion signAture schemE)는 한국형 양자내성암호
(KpqC) 표준화의 격자 기반 전자서명 후보이다. NIST가 표준화한 **Dilithium(ML-DSA)** 과
같은 **Fiat–Shamir with Aborts(FSwA)** 패러다임을 따르되, 다음 설계로 서명·키 크기를
줄인다.

- **Bimodal 분포**: 서명 시 부호 $b\in\{0,1\}$로 $\pm c\mathbf{s}_1$를 선택해 거부
  샘플링 효율을 높임 (BLISS의 bimodal 가우시안 아이디어를 모듈 격자에 적용).
- **초구(hyperball) 균등 샘플링**: 마스킹 nonce $\mathbf{y}$를 이산 하이퍼볼 균등분포에서
  추출 — 가우시안보다 컴팩트한 서명.
- **고정소수점 최적화**: 큰 정수 스케일 $L_N=8192$ 기반 고정소수점 연산.

수학적 안전성은 **Module-LWE**(키)와 **(bimodal self-target) Module-SIS**(위조 불가)
격자 문제의 어려움에 근거한다. 서명/검증키는 Dilithium 대비 각각 최대 39%/25% 작다.

## 2. 파라미터 (레퍼런스 `params.h` 기준)

공통: 다항식 차수 $N=256$, 모듈러스 $q=64513$, 환 $\mathcal{R}_q=\mathbb{Z}_q[x]/(x^{256}+1)$,
비밀 계수 범위 $\eta=1$, 시드 32바이트, CRH 64바이트, 큰 스케일 $L_N=8192$ (13비트).

| 항목 | HAETAE-120 (MODE2) | HAETAE-180 (MODE3) | HAETAE-260 (MODE5) |
|---|---|---|---|
| NIST 보안수준 | 2 | 3 | 5 |
| 모듈 차원 $K$ (행) | 2 | 3 | 4 |
| 모듈 차원 $L$ (열) | 4 | 6 | 7 |
| 비밀 다항식 수 $M=L-1$ | 3 | 5 | 6 |
| 챌린지 해밍무게 $\tau$ | 58 | 80 | 128 |
| 보조 경계 $B_0$ | 9846.02 | 18314.98 | 22343.66 |
| **서명 경계 $B_1$** | **9838.98** | **18307.70** | **22334.95** |
| **검증 경계 $B_2$** | **12777.52** | **21906.65** | **24441.49** |
| $\gamma$ (hyperball 반경 관련) | 48.858 | 57.707 | 55.13 |
| 서명 크기(바이트) | 1474 | 2349 | 2948 |

> **주목 (본 연구와 직결):** 모든 파라미터에서 **$B_1 < B_2$** 이다(예: 120에서
> $9838.98 < 12777.52$, 비율 ≈1.30). 즉 *검증 경계가 서명 경계보다 느슨*하다. 이 때문에
> 거부 샘플링을 우회해 노름이 $[B_1, B_2)$ 구간에 드는 서명은 *검증을 통과*하면서도
> 비밀키 정보를 누설할 수 있고, 단순 "서명 후 검증" 대응이 이를 놓친다. 본 저장소의
> HAETAE-IRV는 *검증 경계가 아니라 서명 경계 $B_1$* 으로 재검사하여 이를 막는다.

## 3. 키 구조

- **공개키** $pk = (\text{seed}_\mathbf{A},\ \mathbf{b})$: 공개 행렬 $\mathbf{A}$는 시드에서
  `unpackA`로 복원(메모리 절약), $\mathbf{b}$는 절단(truncation)으로 짧게 만든 검증키.
- **비밀키** $sk = (\mathbf{s}_1, \mathbf{s}_2, \dots)$: 작은 노름($\eta=1$) 비밀 벡터.
  키생성은 MLWE 샘플로부터 작은 비밀과 대응 공개키를 만들고, 노름 조건을 만족할 때까지
  재샘플링한다. 본 연구의 표적은 $\mathbf{s}_1$이다.

(참고 크기 — 명세 기준: HAETAE-120 공개키 ≈992 B, 비밀키 ≈1408 B.)

## 4. 서명 생성 (개요)

$$\mathbf{z} = \mathbf{y} + (-1)^{b}\, c \cdot \mathbf{s}_1$$

1. 마스킹 nonce $\mathbf{y}$를 이산 하이퍼볼 균등분포에서 샘플링.
   - 시드는 메시지 독립 난수 대신 **비밀키 $K$와 메시지 해시 $\mu$를 결합**해 생성
     (결정론적 경로) 후 `expandYbb`로 확장.
2. 약속 $\mathbf{w} = \text{HighBits}(\mathbf{A}\mathbf{y} \bmod q)$.
3. 챌린지 $c = H(\mu \,\|\, \mathbf{w})$ — 해밍무게 $\tau$의 $\pm1$ 다항식.
4. bimodal 부호 $b \in \{0,1\}$ 선택.
5. 응답 $\mathbf{z} = \mathbf{y} + (-1)^b c\,\mathbf{s}_1$ 계산.
6. **거부 샘플링**: $\|\mathbf{z}\|$ 등이 서명 경계 $B_1$(및 $B_0$)를 벗어나면 1로 복귀.
7. 힌트 $h$ 생성 후 서명 $\sigma = (c, \mathbf{z}, h)$ 출력.

## 5. 서명 검증 (개요)

공개키로 $\mathbf{w}'$를 재구성하고 챌린지를 재계산해 일치/노름을 확인한다. 서명에 담긴
$\mathbf{z}$는 상위비트/하위비트로 분해·압축돼 있어, 힌트 $h$로 제거된 하위 정보를
보정한 뒤 복원한다. 이때 검증은 **느슨한 경계 $B_2$** 로 노름을 확인한다(§2 주목 참조).

## 6. 결함주입 관점에서의 민감점 (본 저장소 연구)

| ID | 결함 효과 | 결과 응답 | 누설 |
|---|---|---|---|
| T1 | $c\cdot\mathbf{s}_1$ 곱셈 스킵 | $\mathbf{z}\approx\mathbf{y}$ | nonce |
| **T2** | $+\mathbf{y}$ 덧셈 스킵 | $\mathbf{z}=(-1)^b c\,\mathbf{s}_1$ | **$\mathbf{s}_1$ 직접(단일 트레이스)** |
| RB | 거부 판정 스킵 | 경계초과 $\mathbf{z}$ | 통계적 키정보 |
| LA | $\mathbf{y}$ 샘플링 loop-abort | 저엔트로피 $\mathbf{y}$ | nonce |

T2에서 $c, L_N$이 공개이므로 NTT 역연산으로 $\mathbf{s}_1$을 직접 복원한다:
$\hat{\mathbf{s}}_1[k] = \mathrm{NTT}(\mathbf{z}/L_N)[k]\cdot\hat c[k]^{-1} \bmod q$.

## 7. 표기 요약

| 기호 | 의미 |
|---|---|
| $N, q$ | 다항식 차수(256), 모듈러스(64513) |
| $\mathbf{A}, \mathbf{b}$ | 공개 행렬, 검증키 |
| $\mathbf{s}_1, \mathbf{s}_2$ | 비밀 벡터 |
| $\mathbf{y}$ | 마스킹 nonce (hyperball) |
| $c$ | 챌린지($\pm1$, 무게 $\tau$) |
| $b$ | bimodal 부호 |
| $\mathbf{z}$ | 응답 벡터(서명 본체) |
| $B_0, B_1, B_2$ | 보조·서명·검증 경계 |
| $L_N$ | 고정소수점 큰 스케일(8192) |

## 8. 참고문헌

- J. H. Cheon, H. Choe, J. Devevey, T. Güneysu, D. Hong, M. Krausz, G. Land, M. Möller,
  D. Stehlé, M. Yi, "HAETAE: Shorter Lattice-Based Fiat-Shamir Signatures," IACR CHES 2024
  (ePrint 2023/624).
- V. Lyubashevsky, "Fiat-Shamir with Aborts," ASIACRYPT 2009 / "Lattice Signatures Without
  Trapdoors," EUROCRYPT 2012.
- L. Ducas, A. Durmus, T. Lepoint, V. Lyubashevsky, "Lattice Signatures and Bimodal
  Gaussians (BLISS)," CRYPTO 2013.
- KpqC: https://kpqc.or.kr — HAETAE 공식 명세/구현.

*수치 출처: HAETAE 레퍼런스 구현 `include/params.h`.*
