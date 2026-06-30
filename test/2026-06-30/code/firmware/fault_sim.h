// SPDX-License-Identifier: MIT
// fault_sim.h — 소프트웨어 라인별 결함주입(축 B, 대응기법 공정 비교)용 결함 지점 ID.
//
// -DFAULT_SIM 빌드에서만 활성. 호스트가 'f' 커맨드로 g_fault_line 을 설정하면
// haetae_sign_cm() 이 해당 슈도코드 라인을 결정론적으로 스킵/변조한다.
// 4개 변형(baseline/double/leeha/irv)이 동일 훅을 공유 → 동일 결함·동일 라인 → 공정 비교.
// (하드웨어 클럭글리치 빌드 CW_TARGET 와는 독립; FAULT_SIM 미정의 시 전부 제거됨.)
#ifndef FAULT_SIM_H
#define FAULT_SIM_H

// 통합 결함 지점 (우리 T1/T2/RB + Lee-Ha 논문 4지점: 시드·부호비트·언패킹·LSB)
#define FL_NONE     0   // 무결함 (golden)
#define FL_SEED     1   // 샘플링 시드 squeeze 스킵 → 시드 0 고정 → 예측가능 y   (Lee-Ha)
#define FL_SIGNBIT  2   // bimodal 부호비트 b 반전                                 (Lee-Ha)
#define FL_UNPACK   3   // 공개행렬 A 언패킹 변조                                  (Lee-Ha)
#define FL_LSB      4   // poly_lsb 추출 스킵 → 다른 챌린지 c                      (Lee-Ha)
#define FL_CS       5   // c*s 곱셈 스킵 → z≈y (nonce 유출)                        (T1)
#define FL_ADDY     6   // +y 덧셈 스킵 → z=(-1)^b c*s (s1 직접 유출)              (T2)
#define FL_REJECT   7   // 거부 판정 스킵 → 경계초과 z 방출                        (RB)

#ifdef FAULT_SIM
extern volatile int g_fault_line;     // 현재 주입할 결함 라인 (FL_*); 호스트 'f' 로 설정
extern volatile int g_fault_oneshot;  // 0=persistent(매 반복 주입), 1=one-shot(첫 발생만=단일 transient)
extern volatile int g_fault_checkskip;// 1=2차 결함: 대응기법의 탐지-후-중단(detect-and-abort) 분기 스킵
#endif

#endif // FAULT_SIM_H
