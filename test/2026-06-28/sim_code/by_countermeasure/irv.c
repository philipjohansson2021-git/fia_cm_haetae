// ===== 대응기법: HAETAE-IRV =====
// 적용 위치: 서명 응답 z 가 확정(거부 통과)된 직후, 힌트/인코딩 이전.
// 방식: M1 c*s1 독립 재계산으로 z=y+(-1)^b c s1 관계 재검증 / M2 서명경계 B1 노름 재검사
//       (거부우회 RB 탐지) / M3 비밀키 체크섬(영속 변조) / M4 잔차 delta 를 무분기 감염.
// 막는 오리지널 성공지점: cs1_mul(T1), add_y(T2), reject(RB), key_mem.
// 못 막음: seed/y/sign_bit/challenge (관계는 성립하되 입력 y·c 가 오염된 경우).
// --- common/sign_fi.c 에서 발췌 (CM_IRV) ---
  /* ===== HAETAE-IRV: 무결성 검증(accept된 z에 대해) ===== */
  if (g_cm==CM_IRV) {
    int delta=0;
    /* M1: c*s1 재계산 -> z1 관계 재검증 */
    polyvecl cs1b; poly chatb=c; poly_ntt(&chatb);
    cs1b.vec[0]=c;
    for (unsigned int ii=1; ii<HAETAE_L; ++ii){
      poly_pointwise_montgomery(&cs1b.vec[ii],&chatb,&s1.vec[ii-1]);
      poly_invntt_tomont(&cs1b.vec[ii]); }
    polyvecl_cneg(&cs1b, b&1);
    polyfixvecl z1b; polyfixvecl_add(&z1b, &y1, &cs1b);
    for (unsigned int ii=0; ii<HAETAE_L && !delta; ++ii)
      for (int k=0;k<HAETAE_N;k++) if (z1.vec[ii].coeffs[k]!=z1b.vec[ii].coeffs[k]){delta=1;break;}
    /* M2: 서명경계 B1 독립 재검사(거부우회 탐지) */
    { uint64_t r=((uint64_t)HAETAE_B1SQ*HAETAE_LN*HAETAE_LN - polyfixveclk_sqnorm2(&z1,&z2))>>63;
      if (r & 1) delta=1; }
    /* M3: 비밀키 체크섬(영속 변조 탐지) */
    if (g_have_golden_ck && g_cur_ck!=g_golden_ck) delta=1;
    if (delta) g_irv_detected=1;   /* 무분기 감염: 출력 무효화(여기선 탐지 플래그) */
  }
