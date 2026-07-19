# verify_s1_pubkey — 복원 s1의 공개키 독립 검증 (리뷰 항목 W2 해소)

복원한 비밀키 `s1`이 옳은지를 **디바이스의 참 s1('s' 스트림) 없이, 오직 공개키(seed_A, b)만으로** 확인한다. 필드의 공격자가 가진 것(공개키 + 복원 s1)과 동일한 정보로 성공을 판정 → "참키 오라클로 판정했다"는 리뷰 반박을 제거.

## 원리 (HAETAE MODE2, D=1 라운딩)

키생성: `b_full = a + A0·s1 + s2 (mod q)`, 공개키는 `b1 = HighBits(b_full) = (b_full − b0)/2` 저장 (`b0∈{-1,0,1}`).
후보 s1에 대해 `w = a + A0·s1_cand` (레퍼런스 산술)를 계산하면:

```
center_q(2·b1 − w) = s2 − b0   (둘 다 작음, |·| ≤ ~3)   ⟺   s1_cand = 참 s1
```

틀린 s1이면 `w`가 mod q 상 사실상 균등 → 모든 계수가 큼. **한 계수만 틀려도** 행렬곱 `A0·s1`이 그 오차를 전 계수로 확산시켜 512/512가 실패한다. 즉 매우 crisp한 공개 판별식.

디바이스 키는 결정론(고정 시드 SHAKE DRBG)이라 호스트가 `randombytes_reset()+crypto_sign_keypair`로 **동일 공개키를 재현**한다. 비밀키는 **self-test 시연용으로만** 언패킹하며, 판별식 자체는 pk만 사용.

## 빌드 (WSL, x86 gcc — 레퍼런스 전체 + 디바이스 DRBG 링크)

```bash
wsl.exe bash -s < build_verify_s1_pubkey.sh      # CRLF 안전(표준입력)
# '\r' 오류 시:  sed -i 's/\r$//' build_verify_s1_pubkey.sh
```

## 사용

```bash
./verify_s1_pubkey                  # self-test (판별식 건전성 증명)
./verify_s1_pubkey recovered_s1.txt # 실제 복원 s1 검증 (768 삼진계수, m*256+k)
```

실제 복원 s1을 파일로 내보내기 (노트북에서 복원 직후):
```python
from haetae_recover_t1 import recover_s1_from_two_traces
r = recover_s1_from_two_traces(z_clean, z_fault, c)   # r['s1ntt'] = [3][256]
from export_s1_for_pubkey import write_coeff_file
write_coeff_file(r['s1ntt'], 'recovered_s1.txt')
```

## Self-test 결과 (2026-07-19, 실행 확인)

```
q=64513  K*N=512  slack T=8
[true s1      ] worst|2b1-w|=     2  bad(>8)=0/512   -> PASS
[-s1 (wrong b)] worst|2b1-w|= 32244  bad(>8)=512/512 -> FAIL
[1-coeff wrong] worst|2b1-w|= 32234  bad(>8)=512/512 -> FAIL
```

참 s1은 잔차 최대 **2**(=s2−b0)로 통과, 임의의 틀린 s1(부호 반전·1계수 오류)은 ~q/2로 전 계수 실패. **판별식이 공개키만으로 정확·강건함이 실증됨.**

## 논문용 서술 (초안)

> 복원한 s1의 정당성은 **공개키 일관성 검사**로 독립 확인한다. HAETAE 키생성 관계 `b = ⌊a + A0 s1 + s2⌉`(공개 `b`는 상위비트)에서, 복원 후보 `s1'`에 대해 `w = a + A0 s1'`를 계산하고 `center_q(2b − w)`가 모든 K·N 계수에서 작은지(= 암묵 `s2`가 작은지) 검사한다. 참 s1은 잔차 ≤ 3으로 전 계수 통과하고, 한 계수라도 틀리면 행렬곱 확산으로 전 계수가 실패한다(실측 최대 잔차 2 대 32244). 이 검사는 **참 비밀키가 아니라 공개키만** 사용하므로, 성공 판정이 실험용 오라클에 의존하지 않는다.

## 파일

- `verify_s1_pubkey.c` — 검증 도구 (레퍼런스 링크)
- `build_verify_s1_pubkey.sh` — 빌드+self-test
- `export_s1_for_pubkey.py` — 복원 s1(NTT) → 계수도메인 파일
- (GitHub 보관 권장: `test/2026-07-18/code/` 또는 새 날짜 폴더)
