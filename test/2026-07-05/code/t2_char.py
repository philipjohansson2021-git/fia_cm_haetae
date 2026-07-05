# -*- coding: utf-8 -*-
# 결함 특성화: 물리 fault 가 z1 을 어떻게 바꾸는지 정량화.
# 기준값 2개(결정론): z1_normal(정상), z1_cleanleak(SW +y 스킵 = 이상적 LN*cs1).
# 각 accepted-fault z1 에 대해: n_changed(정상과 다른 계수), n_cleanleak(이상적 누설값과 일치 = 진짜 y-스킵),
# n_garble(바뀌었지만 누설 아님). 원시 z1 저장 + 분포 요약.
import sys, os, json, time, struct, csv, random, collections
import numpy as np
SCR   = r'C:/Users/NSRSGW/AppData/Local/Temp/claude/c--Users-NSRSGW-ChipWhisperer-chipwhisperer-jupyter-courses-fault-haetae-cm/1435f265-0484-41f5-89af-52c38ea86772/scratchpad'
NBDIR = r'c:/Users/NSRSGW/ChipWhisperer/chipwhisperer/jupyter/courses/fault_haetae_cm'
FW    = r'c:/Users/NSRSGW/ChipWhisperer/chipwhisperer/firmware/mcu/simpleserial-haetae/'
sys.path.insert(0, NBDIR)
import haetae_recover as H
from haetae_recover import read_z1raw, read_cpoly, read_s1ntt, recover_s1_from_z1, agreement

N = 350; W_LO, W_HI = 30, 90; O_LO, O_HI = -20, 20; REPS = [1, 1, 2, 2]
PLATFORM='CW308_STM32F4'
GOLDEN  = bytes.fromhex('ba9f152c607b207fc6512635ba11388c')
LEAK_T2 = bytes.fromhex('63ff5ebfaa6263739651890939cccb48')
FL = {'NONE':0,'SEED':1,'SIGNBIT':2,'UNPACK':3,'LSB':4,'CS':5,'ADDY':6,'REJECT':7}
TRIG_POINT = FL['ADDY']; SIGN_MS = 15000
PROG = os.path.join(SCR,'t2_char_progress.txt'); CSVF=os.path.join(SCR,'t2_char.csv')
NPZ  = os.path.join(SCR,'t2_char_z1.npz'); SUM=os.path.join(SCR,'t2_char_summary.json')

import chipwhisperer as cw, logging
logging.getLogger('ChipWhisperer').setLevel(logging.ERROR)
scope = cw.scope(name='Husky'); target = cw.target(scope, cw.targets.SimpleSerial)
prog = cw.programmers.STM32FProgrammer; scope.default_setup()
def reset_target(s): s.io.nrst='low'; time.sleep(0.05); s.io.nrst='high_z'; time.sleep(0.05)
scope.clock.clkgen_freq=7.37e6; scope.clock.adc_mul=1; scope.io.hs2='clkgen'; time.sleep(0.2)
def ss_echo(t=3000):
    target.flush(); target.simpleserial_write('e', bytearray()); r=target.simpleserial_read('r',16,timeout=t); return bytes(r) if r else None
def ss_sign(t=90000):
    target.flush(); target.simpleserial_write('p', bytearray([0]*16)); r=target.simpleserial_read('r',16,timeout=t); return bytes(r) if r else None
def set_fault(l,o_=0,c=0):
    target.flush(); target.simpleserial_write('f', bytes([l,o_,c])); return target.simpleserial_read('r',1,timeout=3000)
def ss_trig(pt):
    target.flush(); target.simpleserial_write('T', bytes([pt])); return target.simpleserial_read('r',1,timeout=3000)
def flash(h): cw.program_target(scope, prog, FW+h); reset_target(scope); time.sleep(0.5); target.flush()
def recover_target():
    reset_target(scope); time.sleep(0.5); target.flush()
    try: ss_trig(TRIG_POINT)
    except Exception: pass
def set_glitch(d,w,o): scope.glitch.ext_offset=int(d); scope.glitch.width=int(w); scope.glitch.offset=int(o)
def glitch_once(rt=SIGN_MS):
    if scope.adc.state: recover_target()
    scope.arm(); target.flush(); target.simpleserial_write('p', bytearray([0]*16))
    r=target.simpleserial_read_witherrors('r',16, timeout=rt, glitch_timeout=1500)
    try: scope.capture()
    except Exception: pass
    if (not r['valid']) or r['payload'] is None:
        if ss_echo(800) is None: recover_target()
        else: target.flush()
        return 'mute', None
    p=bytes(r['payload']); return ('normal',p) if p==GOLDEN else (('success',p) if p==LEAK_T2 else ('other',p))

# --- setup + baseline flash + WIN ---
scope.io.hs2='clkgen'; flash('haetae-baseline-FSIM-{}.hex'.format(PLATFORM)); set_fault(FL['NONE'],0,0)
assert ss_sign()==GOLDEN, 'GOLDEN mismatch'; ss_trig(TRIG_POINT)
scope.adc.basic_mode='rising_edge'
try: scope.trigger.triggers='tio4'
except Exception: pass
scope.adc.timeout=12; scope.arm(); target.simpleserial_write('p', bytearray([0]*16)); scope.capture()
WIN=int(scope.adc.trig_count); target.simpleserial_read('r',16,timeout=20000)

# --- 기준값 캡처: z1_normal (정상) + z1_cleanleak (SW +y 스킵) + 복구 self-test ---
z1n = read_z1raw(target); cpoly=read_cpoly(target); s1true=read_s1ntt(target)
set_fault(FL['ADDY'],1,0); dcl=ss_sign(); z1cl=read_z1raw(target); set_fault(FL['NONE'],0,0)
rr=recover_s1_from_z1(z1cl, cpoly); selftest,_sgn=agreement(rr['s1ntt'], s1true)
ncl_ref = sum(1 for i in range(1024) if z1cl[i]!=z1n[i])   # 이상적 누설이 바꾸는 계수 수(참고)
print('SETUP ok | WIN=%d | SW-cleanleak digest=%s (==LEAK_T2:%s) | recover self-test=%.1f%% | cleanleak가 바꾸는 계수=%d/1024'
      % (WIN, (dcl or b'').hex()[:8], dcl==LEAK_T2, 100*selftest, ncl_ref), flush=True)

# --- 글리치 모드 전환 ---
scope.glitch.enabled=True; scope.glitch.clk_src='pll'; scope.glitch.output='clock_xor'
scope.glitch.trigger_src='ext_single'; scope.glitch.repeat=1
scope.io.hs2='glitch'; scope.adc.timeout=3
time.sleep(0.2); reset_target(scope); time.sleep(0.5); target.flush(); ss_trig(TRIG_POINT)

# --- 특성화 배치 ---
z1n_a=np.array(z1n); z1cl_a=np.array(z1cl)
cnt=collections.OrderedDict(golden=0,success=0,faulty=0,mute=0,other=0)
faults=[]; saved={}; t0=time.time()
cf=open(CSVF,'w',newline=''); cw2=csv.writer(cf)
cw2.writerow(['ext','width','offset','rep','class','n_changed','n_cleanleak','n_garble','digest']); cf.flush()
for i in range(N):
    e=int(WIN*i/max(N-1,1)); w=random.randint(W_LO,W_HI); o=random.randint(O_LO,O_HI); rep=random.choice(REPS)
    set_glitch(e,w,o); scope.glitch.repeat=int(rep)
    g,p=glitch_once(); cls='golden' if g=='normal' else g
    nch=ncl=ngar=-1
    if p is not None and p!=GOLDEN:
        try:
            z1f=np.array(read_z1raw(target))
            chg = (z1f!=z1n_a)
            nch=int(chg.sum())
            ncl=int(((z1f==z1cl_a)&chg).sum())     # 이상적 누설값과 일치 & 정상과 다름 = 진짜 y-스킵
            ngar=nch-ncl
            faults.append((e,w,o,rep,cls,nch,ncl,ngar)); saved['f%03d'%len(saved)]=z1f
        except Exception:
            pass
    cnt[cls]=cnt.get(cls,0)+1
    cw2.writerow([e,w,o,rep,cls,nch,ncl,ngar, p.hex() if p else '']); cf.flush()
    with open(PROG,'w',encoding='utf-8') as pf:
        pf.write('char shot=%d/%d elapsed=%ds\ncounts=%s\nfaults=%d  (nch,ncl) recent=%s\n'
                 %(i+1,N,int(time.time()-t0),dict(cnt),len(faults),[(f[5],f[6]) for f in faults[-8:]]))
cf.close(); scope.glitch.repeat=1
try:
    if saved: np.savez_compressed(NPZ, z1_normal=z1n_a, z1_cleanleak=z1cl_a, **saved)
except Exception: pass

any_leak = [f for f in faults if f[6]>0]
summary={'N':N,'WIN':WIN,'w':[W_LO,W_HI],'o':[O_LO,O_HI],'reps':REPS,
 'dur_s':round(time.time()-t0,1),'counts':dict(cnt),'self_test_pct':round(100*selftest,1),
 'n_faults':len(faults),'faults_with_cleanleak':len(any_leak),
 'max_ncl':max([f[6] for f in faults],default=0),'max_nch':max([f[5] for f in faults],default=0),
 'faults':faults[:40]}
json.dump(summary, open(SUM,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
try: scope.dis()
except Exception: pass
print('CHAR_RESULT', json.dumps(summary, ensure_ascii=False), flush=True)
