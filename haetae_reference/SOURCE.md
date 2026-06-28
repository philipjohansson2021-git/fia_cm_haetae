# HAETAE 공식 레퍼런스 구현 — 출처 및 라이선스

이 폴더(`haetae_reference/`)는 **HAETAE 공식 레퍼런스 구현을 그대로 포함**한 것입니다.
본 저장소의 결함주입 연구(HAETAE-IRV) 재현을 위해 원본 알고리즘 코드를 함께 둡니다.
**원저작권은 HAETAE 저자에게 있으며, 본 연구진의 코드가 아닙니다.**

## 출처 (Source / Attribution)

- **프로젝트:** HAETAE (Hyperball bimodAl modulE rejecTion signAture schemE)
- **버전:** reference implementation v1.1.2 (원 배포 패키지 `HAETAE-1.1.2`)
- **공식 배포처:**
  - 공식 웹사이트: https://www.kpqc.cryptolab.co.kr/haetae
  - KpqC (한국형 양자내성암호 공모): https://kpqc.or.kr
- **논문:** J. H. Cheon, H. Choe, J. Devevey, T. Güneysu, D. Hong, M. Krausz, G. Land,
  M. Möller, D. Stehlé, M. Yi, *"HAETAE: Shorter Lattice-Based Fiat-Shamir Signatures,"*
  IACR Transactions on CHES (CHES 2024). Cryptology ePrint Archive, Paper 2023/624.
  https://eprint.iacr.org/2023/624

## 라이선스 (License)

- 원본 소스 각 파일은 **`SPDX-License-Identifier: MIT`** 헤더를 가지며 **MIT 라이선스**로
  배포됩니다. 해당 라이선스와 원저작권 표기는 각 파일 헤더에 그대로 유지되어 있습니다.
- 본 폴더의 코드 재배포는 원 MIT 라이선스 조건을 따릅니다. (저장소 루트의 `LICENSE`는
  본 연구진이 작성한 산출물에 적용되며, 이 폴더의 원본 코드에는 위 MIT가 우선합니다.)

## 비고

- 빌드 산출물(`*.o`, `build/` 등)은 제외하고 **소스만** 포함했습니다.
- 빌드 방법은 `haetae_reference/README.md`(원본) 참조 (cmake preset: `haetae-mode2/3/5`).
- 본 연구가 참조/추출한 핵심 파일: `src/sign.c`(서명·검증), `src/ntt.c`·`src/reduce.c`
  (키복원식 검증), `include/params.h`(파라미터·경계값 $B_0/B_1/B_2$).
- 원본과의 일치성: 본 저장소의 core-op 펌웨어와 복원 도구는 이 레퍼런스의 정수 산술과
  비트 단위로 일치함을 검증하였습니다(README 참조).

*마지막 확인: 원 패키지 헤더의 SPDX(MIT) 및 README의 공식 웹사이트 링크 기준.*
