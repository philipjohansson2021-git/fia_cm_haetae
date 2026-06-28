// ===== 대응기법: BASELINE (무방어) =====
// 별도 대응 코드 없음. 계측 서명(common/sign_fi.c)에서 CM_BASE 로 실행.
// 결함 훅만 동작하며, 어떤 검사·무효화도 하지 않는다 -> 모든 키복구 결함이 그대로 방출.
// (참조) common/sign_fi.c 의 결함 훅: seed/y/sign_bit/unpackA/commit/lsb/challenge/cs1(T1)/add_y(T2)/reject(RB)/key_mem.
