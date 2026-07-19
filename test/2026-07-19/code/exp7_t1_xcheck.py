# exp7_t1_xcheck.py — W3: 실제 full-sign 'p' 경로 T1 교차검증 (jig 재생이 아님)
# =====================================================================================
# 목적(리뷰 W3): jig(fire_t1 저장-nonce 재실행) 결과가 "진짜 서명 경로('p')"에서도
#   재현됨을 보여 "jig는 랩 가속기일 뿐"이라는 반박을 제거한다.
#
# 핵심 제약(펌웨어): FL_CS 트리거는 거부 루프의 '매 시도' c·s 마다 토글되고,
#   ext_single 글리치는 '첫' 트리거 에지에만 발사된다. 그리고 g_z1raw(방출 z1)는
#   '채택된 시도'에 대해서만 덤프된다. ⇒ 누설은 선택 메시지가 '첫 시도에 채택'될 때만
#   가능(그때 첫 에지 = 채택 시도의 c·s). 그래서 반드시 1-시도 메시지를 골라야 한다.
#
# 1-시도 선택(결정론·온디바이스): 각 후보 메시지의 무글리치 서명에서 scope.adc.trig_count
#   (트리거 high 사이클수)를 잰다. 1-시도 메시지의 trig_count = 단일 c·s 창(B). K-시도는 ≈K·B.
#   ⇒ 최소 trig_count 메시지가 1-시도이며, 그 값이 곧 c·s WIN. (호스트 벽시계 아님 = 지터 무관.)
#
# 판정: diff%LN==0(ln_exact) + 블록별 참키 일치(복원가능 슬롯=256-#ĉ0 기준).
#   선택 메시지의 c 가 ĉ=0 슬롯이 없고(zero_slots==0) 3블록 모두 복원되면 recovered_s1.txt
#   내보내 ./verify_s1_pubkey 로 공개키 독립검증(W2)까지 실서명 경로에서 연결.
#
# 전제:  EXP7-a 실행  →  %run -i exp7_t1_driver.py  →  %run -i exp7_t1_xcheck.py
#        hex = haetae-baseline-FSIM-T1-*.hex  (FAULT_SIM + T1_CS_ZEROINIT; jig 아님)
import time, collections, random
from tqdm.notebook import trange
from haetae_recover import read_z1raw, read_cpoly, read_s1ntt, ntt, _modq
from haetae_recover_t1 import recover_s1_from_two_traces, verify_s1

_ZERO_K = []   # 선택 메시지 c 의 ĉ[k]=0 슬롯(복원불가). _capture_clean_msg 에서 설정.

def _p_write(msg16): target.flush(); target.simpleserial_write('p', bytes(bytearray(msg16)))
def _p_read(read_timeout=None):
    r = target.simpleserial_read_witherrors('r', 16, timeout=read_timeout or SIGN_MS, glitch_timeout=1500)
    return bytes(r['payload']) if (r['valid'] and r['payload'] is not None) else None

def _clean_trigcount(msg16, adc_to=10):
    """무글리치 FL_CS 서명 1회의 trig_count(트리거 high 사이클) 측정. hs2=clkgen, 글리치 off."""
    if scope.adc.state: recover_target()
    ss_trig(FL['CS']); set_fault(FL['NONE'], 0, 0)
    scope.io.hs2 = 'clkgen'; set_glitch(0, 0, 0); scope.glitch.repeat = 1
    scope.adc.basic_mode = 'rising_edge'; scope.trigger.triggers = 'tio4'
    _adc = scope.adc.timeout; scope.adc.timeout = adc_to
    scope.arm(); _p_write(msg16)
    try: scope.capture()
    except Exception: pass
    d = _p_read()
    tc = int(scope.adc.trig_count)
    scope.adc.timeout = _adc
    return tc, d

def _scan_1attempt(msg_scan=32):
    """후보 메시지들의 trig_count 측정 → 최소(=1-시도) 선택. 반환 (msg16, WIN=B).
       trig_count 는 온디바이스 결정론 지표(벽시계 아님). K-시도≈K·B 로 정량화되어 1-시도 식별."""
    print('[xcheck] 1-시도 메시지 스캔 (온디바이스 trig_count; 최소=단일 c·s 창=1-시도):')
    cand = []
    for m in range(msg_scan):
        msg = [(m & 0xFF)] + [0] * 15
        tc, d = _clean_trigcount(msg)
        if d is None: print('   msg#%d mute' % m); continue
        cand.append((tc, m, d.hex()[:8]))
    assert cand, '모든 메시지 mute — 펌웨어/통신 확인'
    cand.sort()
    B = cand[0][0]
    print('   trig_count 분포(추정 시도수 = tc/B):')
    for tc, m, dh in cand[:12]:
        print('     msg#%-3d tc=%-9d ~%.2f시도  %s' % (m, tc, tc / max(B, 1), dh))
    m0 = cand[0][1]
    have_multi = any(tc > 1.6 * B for tc, _, _ in cand)     # 2·B 이상 군집이 있으면 B=1시도 단위 확증
    if not have_multi:
        print('   ⚠ 2-시도(≈2·B) 군집이 안 보임 → B 가 1-시도라는 확증 약함. msg_scan 늘리거나 바이트 다양화 권장.')
    else:
        print('   ✓ 2·B 이상 군집 확인 → 최소값 B 는 1-시도 단위. 선택 msg#%d 는 1-시도.' % m0)
    print('[xcheck] 선택 msg#%d | WIN(단일 c·s) = %d 사이클' % (m0, B))
    return [(m0 & 0xFF)] + [0] * 15, B

def _capture_clean_msg(msg16):
    """선택 메시지의 깨끗한 서명으로 Z_CLEAN/C_CLEAN/S1_CLEAN/_D0 + ĉ=0 슬롯 설정(무글리치)."""
    global Z_CLEAN, C_CLEAN, S1_CLEAN, _D0, _ZERO_K
    if scope.adc.state: recover_target()
    ss_trig(FL['CS']); set_fault(FL['NONE'], 0, 0)
    scope.io.hs2 = 'clkgen'; set_glitch(0, 0, 0); scope.glitch.repeat = 1
    _p_write(msg16); d0 = _p_read()
    assert d0 is not None, '선택 메시지 깨끗한 서명 실패'
    Z_CLEAN = read_z1raw(target); C_CLEAN = read_cpoly(target); S1_CLEAN = read_s1ntt(target); _D0 = d0
    chat = ntt(C_CLEAN[:]); _ZERO_K = [k for k in range(256) if _modq(chat[k]) == 0]
    print('[xcheck] clean 캡처 완료: z1 다이제스트 =', d0.hex(), '| ĉ=0 슬롯 =', len(_ZERO_K), '(블록당)')
    return d0

def run_t1_fullsign_xcheck(hexname=None, msg_scan=32, N=1500,
                           W_RANGE=(55, 68), O_RANGE=(12, 14), REP_POOL=(2,),
                           E_MIN=0, E_MAX=None, out='t1_fullsign_xcheck',
                           export='recovered_s1.txt', live_every=0):
    """실제 'p' 경로 T1 교차검증 + 블록 누적. FSIM-T1 hex(FAULT_SIM + T1_CS_ZEROINIT).
       ≥1블록 복원 → jig 결과가 실서명 경로에서 재현(W3). ĉ=0 없고 3블록 → recovered_s1.txt(W2+W3)."""
    hexname = hexname or 'haetae-baseline-FSIM-T1-{}.hex'.format(PLATFORM)
    scope.io.hs2 = 'clkgen'; flash(hexname); scope.adc.timeout = 3
    time.sleep(0.2); recover_target(); ss_trig(FL['CS']); set_fault(FL['NONE'], 0, 0)

    msg, win = _scan_1attempt(msg_scan)                 # 온디바이스 trig_count 로 1-시도 선택 + WIN
    _capture_clean_msg(msg)
    if E_MAX is None: E_MAX = win if (1000 < win < 1000000) else 300000
    blk_need = 256 - len(_ZERO_K)                       # 블록별 완전복원 임계(ĉ=0 슬롯 제외)
    scope.io.hs2 = 'glitch'; scope.adc.timeout = 3; recover_target(); ss_trig(FL['CS']); set_fault(FL['NONE'], 0, 0)
    print('[xcheck] ext 스윕 %d~%d | 블록 복원 임계 %d/256 (ĉ=0 %d슬롯 제외)' % (E_MIN, E_MAX, blk_need, len(_ZERO_K)))

    cnt = collections.OrderedDict(golden=0, T1_leak=0, other=0, mute=0); rows = []
    best = 0.0; leaks = []
    block_best = [0, 0, 0]; block_at = [None, None, None]; block_s1 = [None, None, None]
    _adc_t = scope.adc.timeout; scope.adc.timeout = 0.25       # capture 는 정리용 → 대기 짧게(샷 가속)
    it = trange(N, desc='T1 fullsign xcheck') if not live_every else range(N)
    for i in it:
        w = random.randint(*W_RANGE); o = random.randint(*O_RANGE)
        e = random.randint(E_MIN, E_MAX); rep = random.choice(list(REP_POOL))
        if scope.adc.state:
            recover_target(); ss_trig(FL['CS']); set_fault(FL['NONE'], 0, 0)
        set_glitch(e, w, o); scope.glitch.repeat = int(rep)
        scope.arm(); _p_write(msg)
        d = _p_read()
        try: scope.capture()
        except Exception: pass
        if d is None:                                   # mute(크래시) → reprime
            cnt['mute'] += 1; rows.append((int(e), int(w), int(o), int(rep), 'mute', '', ''))
            recover_target(); ss_trig(FL['CS']); set_fault(FL['NONE'], 0, 0)
            if not live_every: it.set_postfix(blk='%d/3' % sum(bm >= blk_need for bm in block_best), **cnt)
            continue
        if d == _D0:                                    # golden(글리치 빗나감) → z1 생략
            cnt['golden'] += 1; rows.append((int(e), int(w), int(o), int(rep), 'golden', '', d.hex()))
            if not live_every: it.set_postfix(blk='%d/3' % sum(bm >= blk_need for bm in block_best), **cnt)
            continue
        try: z1 = read_z1raw(target)
        except Exception: z1 = None
        if z1 is None:
            cnt['other'] += 1; rows.append((int(e), int(w), int(o), int(rep), 'other', '', d.hex()))
            if not live_every: it.set_postfix(blk='%d/3' % sum(bm >= blk_need for bm in block_best), **cnt)
            continue
        rdiff = recover_s1_from_two_traces(Z_CLEAN, z1, C_CLEAN)
        v = verify_s1(rdiff.get('s1ntt'), S1_CLEAN, C_CLEAN)
        ln = rdiff.get('ln_exact', False)
        bm_list = v.get('block_match', [0, 0, 0])       # None-경로 방어(diff%LN≠0 시 [0,0,0])
        agr = v['rate'] if ln else 0.0
        best = max(best, agr)
        cls = 'T1_leak' if (ln and v.get('full')) else 'other'
        cnt[cls] += 1
        rows.append((int(e), int(w), int(o), int(rep), cls, '%.3f' % agr, d.hex()))
        if ln:                                          # diff%LN 게이트 통과분만 블록 누적
            for bi in range(3):
                if bm_list[bi] > block_best[bi]:
                    block_best[bi] = bm_list[bi]; block_at[bi] = (int(e), int(w), int(o), int(rep))
                    if bm_list[bi] >= blk_need: block_s1[bi] = rdiff['s1ntt'][bi]
            if cls == 'T1_leak': leaks.append((int(e), int(w), int(o), int(rep), round(agr, 3)))
            if not live_every and any(bm >= blk_need for bm in bm_list):
                it.write('· 실서명 블록복원 ext=%d w=%d → block_match=%s' % (e, w, bm_list))
        if not live_every:
            it.set_postfix(blk='%d/3' % sum(bm >= blk_need for bm in block_best), best='%.0f%%' % (100 * best), **cnt)
        elif (i + 1) % live_every == 0 or i == N - 1:
            print('[xcheck] %d/%d blk=%d/3 best=%.0f%% | %s' %
                  (i + 1, N, sum(bm >= blk_need for bm in block_best), 100 * best,
                   ' '.join('%s=%d' % (k, val) for k, val in cnt.items())))
        if all(bm >= blk_need for bm in block_best):
            print('★ 3블록 모두 실서명 경로에서 복원 → 조기종료'); break

    scope.glitch.repeat = 1; scope.adc.timeout = _adc_t
    _save(out, rows, cnt, best, leaks, 'fullsign-xcheck')

    nblk = sum(bm >= blk_need for bm in block_best)
    print('\n[xcheck] 결과: 블록 복원 %d/3 (임계 %d/256) | block_best=%s | block_at=%s'
          % (nblk, blk_need, block_best, block_at))
    result = {'blocks': nblk, 'block_best': block_best, 'block_at': block_at,
              'zero_slots': len(_ZERO_K), 'counts': dict(cnt)}
    if nblk >= 1:
        print('  ✅ W3: 실제 full-sign(‘p’) 경로에서 T1 블록 복원 재현 — jig 결과가 실서명 경로로 전이됨.')
    else:
        print('  ⚠ 블록 미복원. 원인 후보: 선택 메시지가 1-시도 아님(scan 재확인)·채택 c·s 미표적·글리치 파라미터.')
        print('    → msg_scan↑, 또는 scan 표에서 tc≈B 인 다른 메시지로 재시도.')
    if len(_ZERO_K) == 0 and nblk == 3 and all(b is not None for b in block_s1):
        try:
            from export_s1_for_pubkey import write_coeff_file
            write_coeff_file([block_s1[0], block_s1[1], block_s1[2]], export)
            print('  ★ 3블록 누적 s1 → %s. 공개키 독립검증:  ./verify_s1_pubkey %s  (W2+W3 동시 폐기)' % (export, export))
            result['export'] = export
        except Exception as ex:
            print('  (export 실패: %s)' % ex)
    elif len(_ZERO_K) > 0:
        print('  주: 선택 메시지 c 에 ĉ=0 슬롯 %d개 → 그 계수는 복원불가라 full-key 공개키검증 불가.' % len(_ZERO_K))
        print('     블록 재현(W3)은 유효. 공개키검증(W2 연계)까지 원하면 ĉ=0 없는 메시지로 재선택(msg_scan↑).')
    return result

# --- 사전점검: xcheck 가 쓰는 EXP7-a/드라이버 전역 확인 ---
_missing_x = [n for n in ('scope', 'target', 'flash', 'recover_target', 'set_glitch', 'set_fault',
                          'ss_trig', 'FL', 'SIGN_MS', 'PLATFORM', '_save', 'LEAK_TH_T1') if n not in globals()]
if _missing_x:
    print('⚠ 전역 누락:', _missing_x, '→ EXP7-a 셀 + %run -i exp7_t1_driver.py 를 먼저 실행하세요.')
else:
    print('로드 완료 — run_t1_fullsign_xcheck()  [W3: 실서명 p 경로 T1 교차검증, FSIM-T1 hex 필요]')
