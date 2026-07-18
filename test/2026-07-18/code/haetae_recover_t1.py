# SPDX-License-Identifier: MIT
# haetae_recover_t1.py — T1(2-trace 차분) 키복원 + "s값까지" 지상진실 검증.
#
#   T1 = c·s 곱셈 스킵 → 결함 응답 z_fault = y1 (nonce). 고정-nonce로
#   깨끗한 응답 z_clean = y1 + (-1)^b·LN·(c·s1) 을 함께 얻으면
#       diff = z_clean - z_fault = (-1)^b·LN·(c·s1)     (y1 정확 상쇄, LN의 정확한 배수)
#   → 기존 T2 역변환 recover_s1_from_z1(diff, c) 로 s1 직접 복원.
#
#   검증은 프록시(일치율 임계)가 아니라 디바이스가 스트리밍하는 '참 s1'과
#   (1) NTT 도메인 정확 일치 개수(/768, 비트정확·권위) +
#   (2) 계수 도메인 실제 s값(역NTT) 대조 로 "s값까지" 확인한다.
#
# 이 파일은 비트정확 T2 코어(haetae_recover.py)를 재사용만 하며 그 파일을 수정하지 않는다.

from haetae_recover import (
    Q, QINV, LN, ZETAS,
    _s32, mont_reduce, ntt, _modq, _inv,
    recover_s1_from_z1,
    read_z1raw, read_cpoly, read_s1ntt,
)

# ---------------------------------------------------------------------------
# 역 NTT (레퍼런스 invntt_tomont 와 비트단위 동일: f = mont^2/256 = -29720).
#   forward ntt() 와 같은 ZETAS 테이블을 k=256 부터 역순(-ZETAS[--k])으로 사용.
#   반환값은 레퍼런스와 동일한 Montgomery(tomont) 표현 → 계수값 표시는 아래
#   _coeff_domain() 에서 참키와 '동일 변환' 후 비교하므로 스케일 차이에 무관하게 일치 검증됨.
# ---------------------------------------------------------------------------
def intt(a):
    a = list(a)
    k = 256
    length = 1
    while length < 256:
        start = 0
        while start < 256:
            k -= 1
            zeta = -ZETAS[k]
            for j in range(start, start + length):
                t = a[j]
                a[j] = t + a[j + length]
                a[j + length] = t - a[j + length]
                a[j + length] = mont_reduce(zeta * a[j + length])
            start = start + 2 * length
        length <<= 1
    f = -29720                      # mont^2/256
    for j in range(256):
        a[j] = mont_reduce(f * a[j])
    return a


def _center(x):
    """mod q 를 [-(q-1)/2, (q-1)/2] 대표원으로."""
    x = _modq(x)
    return x - Q if x > Q // 2 else x


# ---------------------------------------------------------------------------
# T1 2-trace 차분 → s1 복원 (기존 T2 역변환 재사용).
# ---------------------------------------------------------------------------
def diff_traces(z_clean, z_fault):
    """두 원시 z1(각 1024 int32)의 차분. int32 wrap 을 _s32 로 중심화하여
    y1 이 정확 상쇄된 (-1)^b·LN·c·s1 (|.|<2^31) 을 얻는다."""
    assert len(z_clean) == 1024 and len(z_fault) == 1024, \
        "z1 길이는 MODE2 의 L*N=1024 이어야 함(다른 MODE 로 빌드되지 않았는지 확인)"
    return [_s32((z_clean[i] - z_fault[i]) & 0xFFFFFFFF) for i in range(1024)]


def recover_s1_from_two_traces(z_clean, z_fault, c, require_ln=True):
    """T1 차분 복원. z_clean=y1+(-1)^b·LN·c·s1, z_fault=y1 (동일 nonce).
    반환 recover_s1_from_z1 의 dict {'clean_T2', 's1ntt'} 에
        'diff', 'ln_exact'(모든 계수가 LN 의 배수인가=차분 무결성 게이트) 추가.
    주의: T1 차분에서 block0(공개 c)은 양 트레이스에서 상쇄되어 0 → clean_T2=False 가
    정상이다. 성공 판정은 clean_T2 가 아니라 verify_s1() 의 정확 일치로 한다."""
    diff = diff_traces(z_clean, z_fault)
    # 차분 무결성: y1 완전 상쇄 + c·s 완전 제거면 모든 계수가 LN 의 배수.
    ln_exact = all((d % LN) == 0 for d in diff)
    if require_ln and not ln_exact:
        # nonce 불일치 / 부분 스킵 → //LN 이 조용히 쓰레기를 만든다. 하드 거부.
        bad = sum(1 for d in diff if (d % LN) != 0)
        r = {'clean_T2': False, 's1ntt': None, 'diff': diff,
             'ln_exact': False, 'bad_coeffs': bad}
        return r
    r = recover_s1_from_z1(diff, c)
    r['diff'] = diff
    r['ln_exact'] = ln_exact
    return r


# ---------------------------------------------------------------------------
# "s값까지" 지상진실 검증.
#   true_s1ntt: 디바이스 's' 스트림(참 s1, NTT 도메인, 768 int32).
#   rec_s1ntt : recover_s1_from_two_traces()['s1ntt'] (3×256, NTT 도메인, 부호 미정).
#   c         : 챌린지(256). ĉ=NTT(c) 의 0성분(복원 불가 슬롯)을 정확히 계상.
# ---------------------------------------------------------------------------
def verify_s1(rec_s1ntt, true_s1ntt, c):
    """반환 dict:
       sign            : 전역 (-1)^b 부호 '+'/'-' (양쪽 시도 후 우세)
       zero_slots      : ĉ[k]=0 인 복원불가 슬롯 수(3블록 합산)
       recoverable     : 복원가능 슬롯 수 = 768 - zero_slots
       match_recover   : 복원가능 슬롯 중 참키와 정확 일치한 수
       match_768       : 전체 768 중 정확 일치한 수(ĉ=0 슬롯은 자동 불일치)
       full            : (match_recover==recoverable and zero_slots==0) → 완전 복원
       rate            : match_768/768 (기존 agreement 호환)
       coeff_match     : 계수 도메인(역NTT) 정확 일치 수/768 (실제 s값 대조)
       coeff_levels    : 참키 계수 도메인의 서로 다른 중심값들(정상이면 {-1,0,1}에 대응)
    """
    if rec_s1ntt is None:
        return {'sign': None, 'zero_slots': 768, 'recoverable': 0,
                'match_recover': 0, 'match_768': 0, 'full': False,
                'rate': 0.0, 'coeff_match': 0, 'coeff_levels': []}

    chat = ntt(c[:])
    zero_k = [k for k in range(256) if _modq(chat[k]) == 0]
    zero_slots = 3 * len(zero_k)

    def count(sgn):
        m = 0
        for i in range(3):
            for k in range(256):
                if (sgn * rec_s1ntt[i][k]) % Q == _modq(true_s1ntt[i * 256 + k]):
                    m += 1
        return m

    mp, mn = count(1), count(-1)
    sign = '+' if mp >= mn else '-'
    sgn = 1 if mp >= mn else -1
    match_768 = max(mp, mn)

    recoverable = 768 - zero_slots
    match_recover = 0
    block_match = [0, 0, 0]           # 블록별(s1[0],s1[1],s1[2]) 정확 일치 수 → 어느 블록이 누설됐는지
    for i in range(3):
        for k in range(256):
            ok = (sgn * rec_s1ntt[i][k]) % Q == _modq(true_s1ntt[i * 256 + k])
            if ok:
                block_match[i] += 1
                if _modq(chat[k]) != 0:
                    match_recover += 1

    # --- 계수 도메인 실제 s값 대조 (역NTT; rec·참키 '동일 변환' 후 비교) ---
    coeff_match = 0
    coeff_levels = []
    try:
        for i in range(3):
            rec_c = intt([(sgn * rec_s1ntt[i][k]) % Q for k in range(256)])
            tru_c = intt([_modq(true_s1ntt[i * 256 + k]) for k in range(256)])
            rec_c = [_center(v) for v in rec_c]
            tru_c = [_center(v) for v in tru_c]
            coeff_match += sum(1 for k in range(256) if rec_c[k] == tru_c[k])
            for v in tru_c:
                if v not in coeff_levels:
                    coeff_levels.append(v)
        coeff_levels = sorted(coeff_levels)
    except Exception:
        coeff_match = -1  # 표시용 실패(권위 판정은 NTT 도메인)

    return {
        'sign': sign,
        'zero_slots': zero_slots,
        'recoverable': recoverable,
        'match_recover': match_recover,
        'match_768': match_768,
        'full': (match_recover == recoverable and zero_slots == 0),
        'rate': match_768 / 768.0,
        'block_match': block_match,          # [s1[0],s1[1],s1[2]] 각 256 중 일치 수 (누설 블록 식별)
        'coeff_match': coeff_match,
        'coeff_levels': coeff_levels,
    }


def verify_two_traces(z_clean, z_fault, c, true_s1ntt):
    """편의 래퍼: 차분 복원 + s값 검증을 한 번에. 반환 (verify_dict, recover_dict)."""
    r = recover_s1_from_two_traces(z_clean, z_fault, c)
    v = verify_s1(r.get('s1ntt'), true_s1ntt, c)
    v['ln_exact'] = r.get('ln_exact', False)
    return v, r
