// ===== 대응기법: Lee 등 (JKIISC 2026) =====
// 적용 위치: 시드 생성부 / 부호·난수 샘플부 / 서명 종료부.
// 방식: (a) 정상성 검사(XOF 버퍼 퇴화) (b) 시드 독립 재유도 비교
//       (c) 부호/난수 샘플 재계산 비교(부분 이중연산) (d) 서명후검증(harness 에서 Verify 1회).
// 막는 오리지널 성공지점: seed/y/sign_bit/unpackA/commit/lsb/challenge/T1/T2/key_mem.
// 못 막음: reject(RB) — 검증경계 B2 가 서명경계 B1 보다 느슨하기 때문.
// --- common/sign_fi.c 발췌 (CM_LEEHA): 정상성검사 + 시드 재유도 ---
  /* Lee-Ha sanity check: XOF 버퍼 all-zero/all-same 탐지 */
  if (g_cm==CM_LEEHA && fi_buf_degenerate(seedbuf, HAETAE_CRHBYTES)) g_leeha_detected=1;
  /* Lee-Ha partial-double: 시드 독립 재유도 후 비교 */
  if (g_cm==CM_LEEHA){ uint8_t sb2[HAETAE_CRHBYTES]; xof256_state st2;
    xof256_absorb_thrice(&st2,key,HAETAE_SEEDBYTES,rnd,HAETAE_SEEDBYTES,mu,HAETAE_CRHBYTES);
    xof256_squeeze(sb2,HAETAE_CRHBYTES,&st2);
    if(memcmp(sb2,seedbuf,HAETAE_CRHBYTES)) g_leeha_detected=1; }

// --- common/sign_fi.c 발췌 (CM_LEEHA): 부호/난수 샘플 재계산 ---
  /* Lee-Ha partial-double: 부호비트/난수 샘플 재계산 후 비교 */
  if (g_cm==CM_LEEHA){ polyfixvecl y1b; polyfixveck y2b; uint8_t bb=0;
    polyfixveclk_sample_hyperball(&y1b,&y2b,&bb,seedbuf,cb_lh);
    if(bb!=b || memcmp(&y1b,&y1,sizeof(y1)) || memcmp(&y2b,&y2,sizeof(y2))) g_leeha_detected=1; }

// --- 서명후검증은 harness(campaign.c)에서: ---
//   int lr=run(s,&sl,fp,fm,CM_LEEHA);
//   int leeha_det = g_leeha_detected || lr==2 || (lr==0 && vrfy(s,sl)!=0);
