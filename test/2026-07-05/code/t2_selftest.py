# -*- coding: utf-8 -*-
# 정확한 복구 self-test: 같은 fault 서명에서 z1/c/s1 을 읽어(attack_recover) SW clean 누설 복구.
# 기대: agreement ~100%, clean_T2 True.  (char 의 0.1% 가 c-source 버그였는지 판정)
import sys, time
NBDIR = r'c:/Users/NSRSGW/ChipWhisperer/chipwhisperer/jupyter/courses/fault_haetae_cm'
FW    = r'c:/Users/NSRSGW/ChipWhisperer/chipwhisperer/firmware/mcu/simpleserial-haetae/'
sys.path.insert(0, NBDIR)
from haetae_recover import attack_recover, read_z1raw, read_cpoly, read_s1ntt, recover_s1_from_z1, agreement
import chipwhisperer as cw, logging
logging.getLogger('ChipWhisperer').setLevel(logging.ERROR)
PLATFORM='CW308_STM32F4'; FL={'NONE':0,'ADDY':6}
GOLDEN=bytes.fromhex('ba9f152c607b207fc6512635ba11388c'); LEAK_T2=bytes.fromhex('63ff5ebfaa6263739651890939cccb48')
scope=cw.scope(name='Husky'); target=cw.target(scope,cw.targets.SimpleSerial); prog=cw.programmers.STM32FProgrammer
scope.default_setup()
def reset(): scope.io.nrst='low'; time.sleep(0.05); scope.io.nrst='high_z'; time.sleep(0.05)
scope.clock.clkgen_freq=7.37e6; scope.clock.adc_mul=1; scope.io.hs2='clkgen'; time.sleep(0.2)
def wr(c,b=b''): target.flush(); target.simpleserial_write(c,bytearray(b))
def sign(t=90000): wr('p',[0]*16); r=target.simpleserial_read('r',16,timeout=t); return bytes(r) if r else None
def setf(l,o=0,c=0): wr('f',bytes([l,o,c])); return target.simpleserial_read('r',1,timeout=3000)
cw.program_target(scope,prog,FW+'haetae-baseline-FSIM-%s.hex'%PLATFORM); reset(); time.sleep(0.5); target.flush()

# 1) 정상 서명 확인
setf(FL['NONE'],0,0); g=sign(); print('clean sign == GOLDEN :', g==GOLDEN)

# 2) SW +y 스킵(oneshot) → 같은 서명에서 z1/c/s1 읽어 복구
setf(FL['ADDY'],1,0); d=sign()
print('SW T2 sign digest :', (d or b'').hex(), '| == LEAK_T2 :', d==LEAK_T2)
r = attack_recover(target)     # ★ z1·c·s1 모두 이 fault 서명에서
print('attack_recover  -> agreement=%.1f%%  sign=%s  clean_T2=%s' % (100*r['agreement'], r['sign'], r['clean_T2']))

# 3) 추가 확인: same-sign c 로 clean_T2 및 자기일치
z1=read_z1raw(target); c=read_cpoly(target); s1=read_s1ntt(target)
rr=recover_s1_from_z1(z1,c); ag,sg=agreement(rr['s1ntt'],s1)
print('same-sign recover -> agreement=%.1f%% clean_T2=%s' % (100*ag, rr['clean_T2']))
print('block0 z1[:4]=', z1[:4], '| LN*c[:4]=', [8192*c[k] for k in range(4)])
setf(FL['NONE'],0,0)
try: scope.dis()
except Exception: pass
print('SELFTEST_DONE')
