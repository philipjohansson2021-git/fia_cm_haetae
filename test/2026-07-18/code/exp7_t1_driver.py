# exp7_t1_driver.py — 축 A T1(c·s 스킵 → z=y) 2-trace 차분 클럭글리치 드라이버 (Husky + CW308_STM32F4)
# =====================================================================================================
# 개요:
#   T1 = c·s 곱셈을 스킵 → 결함 응답 z_fault = y1 (nonce). 고정-nonce 로 깨끗한
#   z_clean = y1 + (-1)^b·LN·c·s1 을 함께 얻으면 diff = z_clean - z_fault = (-1)^b·LN·c·s1
#   → 기존 T2 역변환으로 s1 복원. 성공은 "디바이스 참 s1 과 계수단위 정확 일치"로만 판정한다.
#
# 사용법 (노트북):
#   1) EXP7-a 셀 실행 (scope/target/flash/recover_target/set_glitch/ss_trig/FL/SIGN_MS/PLATFORM/WIN 정의)
#   2) %run -i exp7_t1_driver.py            ← -i 필수(대화형 전역 재사용)
#   3) [즉시 실행 가능·미수정 펌웨어] run_t1_fullsign()   ← full-sign 'p' 2-trace, FL_CS 트리거
#        · 기존 FAULT_SIM 빌드(haetae-baseline-FSIM-*.hex)로 동작. EDIT 없이 "저항 특성화"부터.
#        · cs pre-zero(EDIT 1) 없으면 c·s 스킵=쓰레기 → diff%LN 게이트가 걸러 대부분 'other'(=저항).
#   4) [클린 누설 인과 대조] run_t1_jig()      ← fast-jig fire_t1, 동일 nonce 보장
#        · 펌웨어 EDIT 1(cs pre-zero) + EDIT 2(fire_t1, 'J' 2) 필요 (아래 T1_FIRMWARE_PATCH.md).
#   5) verify_t1_leak(e,w,o,rep)             ← 발견 파라미터 K회 재현 + s값(NTT 768/768 + 계수도메인) 정밀검증
#
# 판정 임계: 차분이 LN 의 정확한 배수(ln_exact) 이고 참 s1 과 768/768 정확 일치 → T1_leak.
#   (block0=공개 c 는 양 트레이스에서 상쇄되어 0 이 정상 → clean_T2 플래그가 아니라 정확 일치로 판정)
import numpy as np, time, struct, csv, collections, random
import matplotlib.pyplot as plt
from tqdm.notebook import trange

from haetae_recover import read_z1raw, read_cpoly, read_s1ntt, LN
from haetae_recover_t1 import recover_s1_from_two_traces, verify_s1, verify_two_traces

LEAK_TH_T1 = 0.999                         # s1 정확 일치율 임계(768 계수). 완전복원=1.0.

# ---- 상태(prime 시 캡처하는 깨끗한 트레이스/공개값/참키) ----
Z_CLEAN = None      # 깨끗한 응답 z1 = y1 + (-1)^b·LN·c·s1  (원시 fixpoint 1024)
C_CLEAN = None      # 챌린지 c (256)
S1_CLEAN = None     # 참 s1 (NTT, 768)  ← 지상진실 검증용
_D0 = None          # 깨끗한 z1 다이제스트

# ============================ 공용 헬퍼 ============================
def _heatmap(rows, ccol, title, path, xi=0, yi=1, ci=4, xlab='ext_offset', ylab='width'):
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=120)
    for cls, col in ccol.items():
        pts = [(r[xi], r[yi]) for r in rows if r[ci] == cls]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, c=col, s=20, alpha=0.7, edgecolors='none',
                       label='%s (%d)' % (cls, len(pts)))
    ax.set_xlabel(xlab); ax.set_ylabel(ylab); ax.legend(loc='upper right', fontsize=8)
    ax.set_title(title); fig.tight_layout(); fig.savefig(path); plt.show()

def _report_leak(tag, e, w, o, rep, v):
    msg = '%s ext=%d w=%d o=%d rep=%d | s1(NTT)=%d/768' % (tag, e, w, o, rep, v['match_768'])
    if v['zero_slots']:
        msg += ' (복원가능 %d/%d, ĉ=0 손실 %d)' % (v['match_recover'], v['recoverable'], v['zero_slots'])
    if v['coeff_match'] >= 0:
        msg += ' | 계수도메인=%d/768 levels=%s' % (v['coeff_match'], v['coeff_levels'])
    return msg

def _live_dash(rows, cnt, best, done, total, leaks, title):
    """실험 중간 라이브 대시보드: 진행/분류카운트/누설현황 + (ext,width) 산점도. live_every 주기로 호출."""
    from IPython.display import clear_output
    clear_output(wait=True)
    print('[%s] 진행 %d/%d (%.0f%%) | best s1=%.1f%% | %s'
          % (title, done, total, 100.0 * done / max(total, 1), 100 * best,
             '  '.join('%s=%d' % (k, v) for k, v in cnt.items())))
    if leaks:
        print('★ 누설 %d건 (최근 5):' % len(leaks))
        for L in leaks[-5:]:
            print('   ' + (L[5] if len(L) > 5 else 'ext=%d w=%d o=%d rep=%d agr=%.3f' % L[:5]))
    fig, ax = plt.subplots(figsize=(9, 3.3), dpi=100)
    ccol = collections.OrderedDict(golden='0.8', T1_leak='red', other='orange', mute='black')
    for cls, col in ccol.items():
        pts = [(r[0], r[1]) for r in rows if r[4] == cls]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, c=col, s=16, alpha=0.7, edgecolors='none', label='%s(%d)' % (cls, len(pts)))
    ax.set_xlabel('ext_offset'); ax.set_ylabel('width')
    ax.legend(loc='upper right', fontsize=8); ax.set_title(title)
    plt.show()

def _classify(z_fault, d, d0):
    """digest/차분으로 분류 → (cls, agr, v). d0=깨끗한 다이제스트."""
    if d is None:
        return 'mute', None, None
    if d == d0:
        return 'golden', None, None                     # c·s 정상수행(글리치 빗나감)
    if z_fault is None:
        return 'other', None, None
    rdiff = recover_s1_from_two_traces(Z_CLEAN, z_fault, C_CLEAN)   # 차분 복원 1회
    v = verify_s1(rdiff.get('s1ntt'), S1_CLEAN, C_CLEAN)           # s값 지상진실 검증
    if not rdiff.get('ln_exact', False):
        return 'other', 0.0, v                          # y 불일치/부분스킵/쓰레기 → 차분 무결성 실패
    agr = v['rate']
    if agr >= LEAK_TH_T1 and v['full']:
        return 'T1_leak', agr, v
    return 'other', agr, v

# ============================ full-sign 'p' 경로 (미수정 FSIM 펌웨어에서 실행) ============================
def _sign_read(glitch=False, read_timeout=None):
    """전체서명 'p'(고정-nonce) 1회. glitch=True 면 FL_CS 트리거에서 자동 글리치.
       반환 (digest16 or None, z1raw(1024) or None)."""
    read_timeout = read_timeout or SIGN_MS
    if scope.adc.state:
        recover_target(); ss_trig(FL['CS'])
    if glitch:
        scope.arm()
    target.flush(); target.simpleserial_write('p', bytearray([0] * 16))
    r = target.simpleserial_read_witherrors('r', 16, timeout=read_timeout, glitch_timeout=1500)
    if glitch:
        try: scope.capture()
        except Exception: pass
    if (not r['valid']) or r['payload'] is None:
        return None, None
    d = bytes(r['payload'])
    try:
        z1 = read_z1raw(target)
    except Exception:
        z1 = None
    return d, z1

def t1_setup_fullsign(hexname=None):
    """FSIM 펌웨어 flash + FL_CS 트리거 선택 + 깨끗한 트레이스/공개값/참키 캡처."""
    global Z_CLEAN, C_CLEAN, S1_CLEAN, _D0
    hexname = hexname or 'haetae-baseline-FSIM-{}.hex'.format(PLATFORM)
    scope.io.hs2 = 'clkgen'; flash(hexname); scope.io.hs2 = 'glitch'; scope.adc.timeout = 3
    time.sleep(0.2); recover_target(); ss_trig(FL['CS']); scope.glitch.repeat = 1
    d0, z1 = _sign_read(glitch=False)
    assert d0 is not None and z1 is not None, '깨끗한 서명 실패 — 펌웨어/키/SIGN_MS 확인'
    Z_CLEAN = z1; C_CLEAN = read_cpoly(target); S1_CLEAN = read_s1ntt(target); _D0 = d0
    print('[fullsign] 깨끗한 z1 다이제스트 =', d0.hex())
    print('           트리거지점 = FL_CS(c·s), z1/c/s1 캡처 완료 (참 s1 768계수 확보)')
    return d0

def t1_measure_win_fullsign():
    """FL_CS(c·s) 트리거 창 측정 → ext_offset 스윕 상한."""
    scope.io.hs2 = 'clkgen'; scope.adc.basic_mode = 'rising_edge'
    scope.trigger.triggers = 'tio4'; scope.adc.timeout = 6; recover_target(); ss_trig(FL['CS'])
    scope.arm(); target.flush(); target.simpleserial_write('p', bytearray([0] * 16))
    try: scope.capture()
    except Exception: pass
    target.simpleserial_read_witherrors('r', 16, timeout=SIGN_MS, glitch_timeout=1500)
    win = int(scope.adc.trig_count)
    scope.io.hs2 = 'glitch'; scope.adc.timeout = 3; recover_target(); ss_trig(FL['CS'])
    print('[fullsign] c·s WIN =', win)
    return win

def run_t1_fullsign(hexname=None, N=400, W_RANGE=(30, 75), O_RANGE=(-15, 15),
                    E_MIN=0, E_MAX=None, REP_POOL=(1, 1, 2), out='t1_fullsign', live_every=25):
    """full-sign 'p' 2-trace T1 스윕. 미수정 FSIM 펌웨어에서 즉시 실행 가능.
       cs pre-zero(EDIT 1) 미적용 시 c·s 스킵=쓰레기 → diff%LN 게이트가 걸러 'other'(저항 특성화).
       EDIT 1 적용 시 loop-abort → z=y → T1_leak. 물리 렌즈: 클린은 cs1 외곽루프 진입 밴드에서만.
       live_every>0 : 그 주기마다 라이브 대시보드(산점도+진행+누설) 갱신. 0 = tqdm 진행바만(가장 빠름)."""
    t1_setup_fullsign(hexname)
    win = t1_measure_win_fullsign()
    if E_MAX is None: E_MAX = win if (50 < win < 300000) else 60000   # trig_count 오측정(거대값) 방어 클램프
    print('  ext 스윕 %d~%d (물리 렌즈: c·s 외곽루프 진입점 부근이 클린 밴드; 필요시 좁혀 재스윕)' % (E_MIN, E_MAX))

    cnt = collections.OrderedDict(golden=0, T1_leak=0, other=0, mute=0); rows = []; best = 0.0; leaks = []
    use_bar = not live_every
    it = trange(N, desc='T1 fullsign') if use_bar else range(N)
    for i in it:
        w = random.randint(*W_RANGE); o = random.randint(*O_RANGE)
        e = random.randint(E_MIN, E_MAX); rep = random.choice(list(REP_POOL))
        set_glitch(e, w, o); scope.glitch.repeat = int(rep)
        d, z1 = _sign_read(glitch=True)
        cls, agr, v = _classify(z1, d, _D0)
        if agr is not None: best = max(best, agr)
        if cls == 'T1_leak':
            leaks.append((int(e), int(w), int(o), int(rep), round(agr, 3), _report_leak('T1_leak', e, w, o, rep, v)))
        cnt[cls] += 1
        rows.append((int(e), int(w), int(o), int(rep), cls,
                     ('%.3f' % agr) if agr is not None else '', d.hex() if d else ''))
        if use_bar:
            if cls == 'T1_leak': it.write('★ ' + leaks[-1][5])
            elif cls == 'other' and agr and agr > 0:
                it.write('· 부분누설 ext=%d w=%d → s1 %.1f%%%s' %
                         (e, w, 100 * agr, '' if (v and v['ln_exact']) else ' (diff%LN≠0)'))
            it.set_postfix(best='%.0f%%' % (100 * best), **cnt)
        elif (i + 1) % live_every == 0 or i == N - 1:
            _live_dash(rows, cnt, best, i + 1, N, leaks, 'T1 fullsign (c*s)')
    scope.glitch.repeat = 1
    _save(out, rows, cnt, best, [L[:5] for L in leaks], 'fullsign')
    return dict(cnt), rows

# ============================ [글리치 없이] SW T1 모델로 복원 체인 검증 ============================
def _sign_msg(msg16, fault_line=None, read_timeout=None):
    """전체서명 'p'(무글리치). fault_line 주면 SW 오류(FL_*) 주입. 반환 (digest16, z1raw) 또는 (None,None)."""
    read_timeout = read_timeout or SIGN_MS
    if scope.adc.state:
        recover_target(); ss_trig(FL['CS'])
    set_fault(fault_line if fault_line is not None else FL['NONE'], 0, 0)
    target.flush(); target.simpleserial_write('p', bytes(bytearray(msg16)))
    r = target.simpleserial_read_witherrors('r', 16, timeout=read_timeout, glitch_timeout=1500)
    if (not r['valid']) or r['payload'] is None:
        return None, None
    d = bytes(r['payload'])
    try: z1 = read_z1raw(target)
    except Exception: z1 = None
    return d, z1

def validate_t1_chain_sw(hexname=None, tries=8):
    """[글리치 불필요] 디바이스 SW T1 모델(FL_CS: c·s=0 → z=y)로 T1 복원 체인 전체를 실디바이스에서 확정.
       메시지 M 마다: 깨끗한 서명 z_clean(=y+LN·cs) + FL_CS 서명 z_fault(=y) → 차분(z_clean−z_fault)=LN·cs
       → recover_s1_from_z1 → s1 역산 → 참키(‘s’ 스트림) 768/768 대조.
       주의: 두 서명이 거부루프에서 같은 시도를 채택해야 y 가 상쇄(diff%LN==0). M 을 바꿔가며 성립 케이스 탐색.
       (동일-nonce 를 무조건 보장하려면 jig(EDIT 2). 복원 수학 자체는 합성검증에서 이미 768/768.)"""
    hexname = hexname or 'haetae-baseline-FSIM-{}.hex'.format(PLATFORM)
    scope.io.hs2 = 'clkgen'; flash(hexname); recover_target(); ss_trig(FL['CS']); set_fault(FL['NONE'], 0, 0)
    print('[SW검증] baseline FSIM · 글리치 없음 · T1 복원 체인(y추출→z−y=cs→s역산) 실디바이스 검증')
    ok = None
    for t in range(tries):
        msg = [(t & 0xFF)] + [0] * 15
        d_c, z_clean = _sign_msg(msg, FL['NONE'])
        if z_clean is None:
            print('  msg#%d: clean 서명 mute' % t); continue
        c = read_cpoly(target); s1t = read_s1ntt(target)     # clean 서명의 c·참s1 (FL_CS 가 g_* 덮기 전에)
        d_f, z_fault = _sign_msg(msg, FL['CS'])
        if z_fault is None:
            print('  msg#%d: FL_CS 서명 mute' % t); continue
        v, r = verify_two_traces(z_clean, z_fault, c, s1t)
        tag = 'LN배수 OK' if v['ln_exact'] else 'diff%LN≠0(두 서명이 다른 시도 채택→y 미상쇄)'
        print('  msg#%d: %-32s | s1 NTT=%d/768 계수=%d/768 full=%s sign=%s zero(ĉ=0)=%d'
              % (t, tag, v['match_768'], v['coeff_match'], v['full'], v['sign'], v['zero_slots']))
        if v['ln_exact'] and v['full']:
            print('  ★ 확정: 디바이스 z_clean 과 (SW로 추출한) y 의 차분 → cs → s1 역산 → 참 비밀키 768/768 일치.')
            print('    → T1 공격의 복원 반쪽(y→cs→s)이 실디바이스에서 성립. 남은 것은 물리 y 추출(클럭글리치+EDIT1).')
            ok = (t, v); break
    set_fault(FL['NONE'], 0, 0)
    if ok is None:
        print('  ⚠ %d개 메시지 모두에서 clean/FL_CS 가 같은 시도를 채택 못함(거부루프 발산 → y 미상쇄).' % tries)
        print('    → tries 를 늘리거나, 동일-nonce 보장 jig(EDIT 2) 사용. 복원 수학은 합성검증에서 이미 768/768 확인됨.')
    return ok

# ============================ fast-jig 경로 (EDIT 1+2 필요, 동일 nonce 보장) ============================
def ss_jig_t1(mode, timeout=None):
    """'J' 지그. mode 0=prime(정상 서명+상태저장 ~8s), 2=fire_t1(c·s 재실행 ~ms). 반환 z1 다이제스트 또는 None.
       (mode 2 는 펌웨어 EDIT 2: haetae_axisa_fire_t1 필요)"""
    target.flush(); target.simpleserial_write('J', bytes([mode & 3]))
    tmo = (timeout or SIGN_MS) if mode == 0 else 3000
    r = target.simpleserial_read_witherrors('r', 16, timeout=tmo, glitch_timeout=1500)
    if (not r['valid']) or r['payload'] is None:
        return None
    return bytes(r['payload'])

def _reprime_t1():
    recover_target(); ss_trig(FL['CS']); return ss_jig_t1(0)

def t1_prime_jig():
    """prime → 참키/공개값 캡처. 그리고 [필수 게이트] 무글리치 fire_t1 이 prime z1 과
       바이트동일한지 확인(=fire_t1 이 동일 y1/c/s 를 재현 → 차분에서 y1 정확 상쇄 보장)."""
    global Z_CLEAN, C_CLEAN, S1_CLEAN, _D0
    d0 = ss_jig_t1(0)
    assert d0 is not None, 'prime 실패 — 펌웨어(AXISA_JIG)/키/SIGN_MS 확인'
    z_prime = read_z1raw(target); C_CLEAN = read_cpoly(target); S1_CLEAN = read_s1ntt(target)
    set_glitch(0, 0, 0); scope.glitch.repeat = 1
    d_fire = ss_jig_t1(2)                                   # 무글리치 fire_t1
    assert d_fire is not None, 'fire_t1 실패 — 펌웨어 EDIT 2("J" 2) 미적용?'
    z_clean_fire = read_z1raw(target)
    assert d_fire == d0 and z_clean_fire == z_prime, \
        '무글리치 fire_t1 ≠ prime z1 — fire_t1 이 동일 nonce/c/s 를 재현하지 못함(EDIT 2 저장 로직 확인). 스윕 중단.'
    Z_CLEAN = z_clean_fire; _D0 = d0                        # 클린=fire_t1 경로(결함과 동일 코드경로)
    print('[jig] prime OK, 무글리치 fire_t1 == prime z1 (동일 nonce 보장) | d0 =', d0.hex())
    return d0

def t1_measure_win_jig():
    scope.io.hs2 = 'clkgen'; scope.adc.basic_mode = 'rising_edge'
    scope.trigger.triggers = 'tio4'; scope.adc.timeout = 6; d0 = _reprime_t1()
    set_glitch(0, 0, 0); scope.glitch.repeat = 1
    scope.arm(); target.flush(); target.simpleserial_write('J', bytes([2]));
    try: scope.capture()
    except Exception: pass
    target.simpleserial_read_witherrors('r', 16, timeout=3000, glitch_timeout=1500)
    win = int(scope.adc.trig_count)
    scope.io.hs2 = 'glitch'; scope.adc.timeout = 3; _reprime_t1()
    print('[jig] fire_t1 c·s WIN =', win)
    return win

def run_t1_jig(hexname=None, N=400, W_RANGE=(30, 75), O_RANGE=(-15, 15),
               E_MIN=0, E_MAX=None, REP_POOL=(1, 1, 2), out='t1_jig', live_every=25):
    """fast-jig fire_t1 T1 스윕. 동일 nonce 보장(차분 y1 정확 상쇄). EDIT 1+2 펌웨어 필요.
       live_every>0 : 그 주기마다 라이브 대시보드 갱신. 0 = tqdm 진행바만."""
    hexname = hexname or 'haetae-JIG-T1-fused-{}.hex'.format(PLATFORM)
    scope.io.hs2 = 'clkgen'; flash(hexname); scope.io.hs2 = 'glitch'; scope.adc.timeout = 3
    time.sleep(0.2); recover_target(); ss_trig(FL['CS']); scope.glitch.repeat = 1
    t1_prime_jig()
    win = t1_measure_win_jig(); _reprime_t1()
    if E_MAX is None: E_MAX = win if (50 < win < 300000) else 60000   # trig_count 오측정(거대값) 방어 클램프
    print('  ext 스윕 %d~%d' % (E_MIN, E_MAX))

    cnt = collections.OrderedDict(golden=0, T1_leak=0, other=0, mute=0); rows = []; best = 0.0; leaks = []
    _adc_t = scope.adc.timeout; scope.adc.timeout = 0.25   # capture 는 정리용 → 대기 짧게(3s→0.25s, 샷 가속)
    use_bar = not live_every
    it = trange(N, desc='T1 jig') if use_bar else range(N)
    for i in it:
        w = random.randint(*W_RANGE); o = random.randint(*O_RANGE)
        e = random.randint(E_MIN, E_MAX); rep = random.choice(list(REP_POOL))
        if scope.adc.state: _reprime_t1()
        set_glitch(e, w, o); scope.glitch.repeat = int(rep)
        scope.arm(); target.flush(); target.simpleserial_write('J', bytes([2]))
        try: scope.capture()          # fire_t1 ~26ms: 트리거 즉시 발생 → capture-first 로 빠르게 잡음(정리대기 없음)
        except Exception: pass
        r = target.simpleserial_read_witherrors('r', 16, timeout=1000, glitch_timeout=400)
        d = bytes(r['payload']) if (r['valid'] and r['payload'] is not None) else None
        if d is None:
            cls, agr, v = 'mute', None, None; _reprime_t1()
        elif d == _D0:
            cls, agr, v = 'golden', None, None        # 깨끗한 서명 → z1 안 읽음(64청크 스트리밍 생략, 대폭 가속)
        else:
            z1 = read_z1raw(target)                    # 다이제스트 변한 것만 z1 스트리밍 후 차분/복원
            cls, agr, v = _classify(z1, d, _D0)
            if agr is not None: best = max(best, agr)
            if cls == 'T1_leak':
                leaks.append((int(e), int(w), int(o), int(rep), round(agr, 3), _report_leak('T1_leak', e, w, o, rep, v)))
        cnt[cls] += 1
        rows.append((int(e), int(w), int(o), int(rep), cls,
                     ('%.3f' % agr) if agr is not None else '', d.hex() if d else ''))
        if use_bar:
            if cls == 'T1_leak': it.write('★ ' + leaks[-1][5])
            it.set_postfix(best='%.0f%%' % (100 * best), **cnt)
        elif (i + 1) % live_every == 0 or i == N - 1:
            _live_dash(rows, cnt, best, i + 1, N, leaks, 'T1 jig (c*s)')
    scope.glitch.repeat = 1; scope.adc.timeout = _adc_t
    _save(out, rows, cnt, best, [L[:5] for L in leaks], 'jig')
    return dict(cnt), rows

# ============================ 재현 검증(paper-grade) + 저장 ============================
def verify_t1_leak(e, w, o, rep=1, K=30, path='jig'):
    """발견된 파라미터를 K회 재현하여 s값 복원의 안정성/정확성 정밀 검증.
       각 시도: 차분 → verify_s1 (NTT 768/768 + 계수도메인). path='jig'|'fullsign'."""
    fire = (lambda: (ss_jig_t1(2), read_z1raw(target))) if path == 'jig' else None
    print('=== verify_t1_leak: ext=%d w=%d o=%d rep=%d × %d회 (path=%s) ===' % (e, w, o, rep, K, path))
    if path == 'jig': _reprime_t1()
    set_glitch(e, w, o); scope.glitch.repeat = int(rep)
    oks = 0; rates = []; detail = None
    for _ in trange(K, desc='verify'):
        if scope.adc.state:
            _reprime_t1() if path == 'jig' else (recover_target(), ss_trig(FL['CS']))
        if path == 'jig':
            scope.arm(); target.flush(); target.simpleserial_write('J', bytes([2]))
            r = target.simpleserial_read_witherrors('r', 16, timeout=3000, glitch_timeout=1500)
            try: scope.capture()
            except Exception: pass
            d = bytes(r['payload']) if (r['valid'] and r['payload'] is not None) else None
            z1 = read_z1raw(target) if d is not None else None
        else:
            d, z1 = _sign_read(glitch=True)
        if d is None or z1 is None:
            if path == 'jig': _reprime_t1()
            continue
        v = verify_s1(recover_s1_from_two_traces(Z_CLEAN, z1, C_CLEAN).get('s1ntt'), S1_CLEAN, C_CLEAN)
        rd = recover_s1_from_two_traces(Z_CLEAN, z1, C_CLEAN)
        if rd.get('ln_exact') and v['rate'] >= LEAK_TH_T1 and v['full']:
            oks += 1; detail = v
        rates.append(v['rate'])
    scope.glitch.repeat = 1
    print('완전복원(768/768) 성공: %d/%d (%.0f%%) | 평균 s1 일치율 %.1f%%' %
          (oks, K, 100 * oks / K, 100 * (sum(rates) / len(rates) if rates else 0)))
    if detail:
        print('  대표 성공: NTT %d/768, 계수도메인 %d/768, 참키 계수레벨 %s, 부호 %s'
              % (detail['match_768'], detail['coeff_match'], detail['coeff_levels'], detail['sign']))
        print('  → 디바이스 참 비밀키 s1 을 계수단위로 정확 복원 확인.')
    return oks, rates

def _save(out, rows, cnt, best, leaks, tag):
    with open(out + '.csv', 'w', newline='') as f:
        wr = csv.writer(f); wr.writerow(['ext', 'width', 'offset', 'repeat', 'class', 'agreement', 'digest'])
        wr.writerows(rows)
    _heatmap(rows, collections.OrderedDict(golden='0.8', T1_leak='red', other='orange', mute='black'),
             'Axis-A c*s sweep [%s] (red=T1_leak: s1 recovered)' % tag, 'fig_%s_map.png' % out)
    print('DONE [%s]:' % tag, dict(cnt), '| best s1=%.1f%%' % (100 * best), '| leaks:', leaks[:5])
    print('  saved %s.csv, fig_%s_map.png' % (out, out))

# --- 사전점검: 기존 EXP7-a 부트스트랩 전역이 로드돼 있는지(%run -i 로 재사용) ---
_g = globals()
_missing = [n for n in ('scope', 'target', 'flash', 'recover_target', 'set_glitch',
                        'ss_trig', 'FL', 'SIGN_MS', 'PLATFORM') if n not in _g]
if _missing:
    print('⚠ EXP7-a 전역 누락:', _missing,
          '→ Lab_HAETAE_F4_EXP7_AxisA.ipynb 의 EXP7-a 셀을 먼저 실행하고  %run -i exp7_t1_driver.py  로 재로드')
else:
    print('사전점검 OK — EXP7-a 전역 재사용 확인 (scope/target/flash/set_glitch/ss_trig/FL/SIGN_MS/PLATFORM)')
print('로드 완료 — validate_t1_chain_sw()[글리치X, 체인검증]  /  run_t1_fullsign()  /  run_t1_jig()  /  verify_t1_leak(...)')
print('전제: EXP7-a 실행 완료 + TRIG_POINT=FL["CS"]. fullsign=기존 haetae-baseline-FSIM-*.hex 로 즉시 실행(저항 특성화).')
print('      클린 T1 누설(인과 대조)은 펌웨어 EDIT 1(cs pre-zero)+EDIT 2(fire_t1) 필요 → T1_FIRMWARE_PATCH.md')
