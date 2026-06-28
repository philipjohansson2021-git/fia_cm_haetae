// ===== 대응기법: 전체 이중연산 (Double Computation) =====
// 적용 위치: 서명 전체를 감싸는 래퍼.
// 방식: 서명을 2회 수행(여기선 결함 실행 vs 무결함 실행) 후 출력 비교, 불일치 시 폐기.
// 막는 오리지널 성공지점: 일시적(transient) 결함 대부분.
// 못 막음: key_mem(영속 변조 - 두 실행 동일).
// --- harness(campaign.c)에서 모델링 ---
    // double: 일시적 결함이면 두 실행 상이->탐지. 영속(key_mem)은 미탐.
    int double_det = (faulty && fp!=FP_KEYMEM) ? 1 : (br==2?1:0);
