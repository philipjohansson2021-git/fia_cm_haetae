# DIL-09-U2 — $\Delta z$ · MLWE→RLWE · 격자 복구

단위: **DIL-09-U2**  
논문: [9] §3.2–§5  
상태: **presented** (다회 fault·수치 예·MLWE→RLWE 슬라이드 반영)

## 요지

1. $\Delta z = c(s_1[i]-s_1[j])$ 관계 $\ell-1$ 개
2. 공개 $t=As_1+s_2$ 와 결합 → MLWE$(k,\ell)$ → RLWE 축소
3. BKZ 등 lattice reduction; $t$ full public vs $t_1$ only
4. hints / side-information (Dachman-Soled et al.) 가속

## 비판

- [9] instruction skip 실측 없음
- $t_1$ only 시 level V 만 full recovery 보고 (컴퓨팅 한계 주장)
