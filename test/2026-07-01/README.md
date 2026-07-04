# 2026-07-01 — 축 A(하드웨어 클럭글리치) 실현성 셋업 + AES 리그 검증

STM32F4(CW308+Husky, HSE 직결 7.37MHz)에서 **실제 클럭글리치로 T2를 유발**하려는 축 A 실험을
집중적으로 디버깅하고, 도구·펌웨어·판정법을 확립한 날. HAETAE 축 A의 최종 LEAK은 아직 **진행 중**.

## 무엇을 했나

### 1) AES 클럭글리치로 "리그 정상 동작" 검증 (핵심 성과)
- 알려진-정상 예제 `simpleserial-aes`(TINYAES128C)로 이 리그가 클럭글리치를 실제로 유발하는지 확인.
- 노트북: `code/Lab_AES_Glitch_Check_F4.ipynb` (랜덤 파라미터 탐색 + 실시간 파형/진행바 + Lab1_1B DFA 키복원).
- **결과: 리그 정상.** width≈50에서 40회 중 13회 clean fault(틀린 유효 암호문), 6회만 crash. 단일바이트 결함도 관찰(DFA 이상적).
- **결정적 발견: Husky `clock_xor` width sweet spot ≈ 40~70(≈50).** 그동안 HAETAE에 width 3~8(20배 작음)을 줘서 전부 crash로 오판했던 것이 실패 원인이었음.

### 2) 펌웨어: "트리거 = 공격지점" 기능 추가
- `haetae_sign_cm.c`에 `g_trig_line` + `TRIG_HI/LO(pt)`/`TRIG_BROAD_HI/LO()` 매크로. 7개 지점(UNPACK/SEED/SIGNBIT/LSB/CS/ADDY/REJECT) 각 연산 직전·직후에 트리거 삽입.
- 호스트 **`T` 커맨드**(`cmd_trigline`, `simpleserial-haetae.c`): 지점 선택(0=전체 c·s~+y, FL_*=그 연산만). → 트리거 윈도우 축소 → `ext_offset≈0`+`width~50` 정밀 타격. 축 B의 `f`(공격지점 선택)와 1:1 통일.
- baseline/double/leeha/irv FSIM hex를 새 펌웨어로 WSL 재빌드.

### 3) HAETAE 축 A 노트북 개편 → 독립 노트북으로 분리
- `code/Lab_HAETAE_F4_EXP7_AxisA.ipynb` (자체완결). 메인 노트북(`Lab_HAETAE_F4_FullSign_v1`)에서 EXP7 제거(중복 해소).
- 반영: **트리거@ADDY** / **랜덤 탐색(width~50)** / **복원율(agreement) 기반 LEAK 판정** / `glitch_once`는 **시리얼 먼저 읽고 capture 뒤에**(capture 타임아웃 간섭 제거) / tqdm 진행바(그래프는 끝 1회).
- 구성: EXP7-a(셋업)·b2(width밴드 진단)·b(랜덤 탐색)·c(정밀화)·d(4변형 비교+막대그래프).

## 결과 / 관찰 (2026-07-01 시점)
- **AES 축 A: 성공** — 리그·배선·Husky 정상, width~50 확정, DFA 키복원 경로 확보.
- **HAETAE 축 A: 진행 중(미확정).**
  - 트리거를 +y로 좁혀 `WIN(ADDY)=15,568` 사이클(전체 38k → +y만).
  - **width 35~70은 +y를 crash(mute)** 시키는 경향. +y는 fixpoint 다항식 벡터덧셈(~15.5k cycle)이라, 단일 클럭글리치로 **y 전체 제거(clean T2)** 는 어려움(명령어 1개만 교란).
  - 따라서 판정을 exact `LEAK_T2` 다이제스트 → **결함 응답 z1의 s1 복원율(agreement)** 로 변경(부분누설 정량화). HAETAE HW LEAK(복원율≥99%)은 아직 미포착.
- **핵심 교훈**: (a) width 스케일(~50), (b) 트리거를 공격지점에 배치, (c) `scope.capture()` 의존 금지(시리얼로 판정), (d) hs2='glitch' 전환 후 리셋 필수, (e) 판정은 복원율.

## 다음
- HAETAE 축 A: EXP7-b2로 +y clean-fault 밴드(더 작은 width) 탐색 → 없으면 `TRIG_POINT=FL[CS]`(T1, NTT 산술) 시도 또는 전압글리치.
- **키복원 실증은 이미 축 B(2026-06-30, SW 주입, s1 100%)로 확보**되어 있으므로, 축 A는 "물리 실현성/글리치 민감도" 보강 역할.

## 파일
```
code/
├─ Lab_HAETAE_F4_EXP7_AxisA.ipynb   축 A(HW 클럭글리치, 트리거=공격지점, 랜덤, 복원율 판정)
├─ Lab_AES_Glitch_Check_F4.ipynb    AES 리그 검증(width~50, DFA 키복원)
├─ haetae_recover.py                T2 z1→s1 복원
└─ firmware/                        haetae_sign_cm.c(‘T’ 트리거)·simpleserial-haetae.c·fault_sim.h·makefile
```
> `T` 트리거 포함 최신 펌웨어로 `haetae-*-FSIM-*.hex` 재빌드 필요(메인 노트북 BUILD 또는 WSL make).
