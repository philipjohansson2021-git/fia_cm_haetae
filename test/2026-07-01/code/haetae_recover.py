# SPDX-License-Identifier: MIT
# haetae_recover.py — T2(직접 추출) 키복원 + 디바이스 스트리밍 유틸 (전체서명 F4 실험용).
#
#   직접 추출(T2, +y 스킵): z1 = LN * (c·s1) (mod q).  c 공개 → 역연산으로 s1 직접.
#     s1ntt[k] = NTT(z1_block/LN)[k] · ĉ[k]^{-1} (mod q),  ĉ = NTT(c).
#   레퍼런스 정수산술(Montgomery/NTT)과 비트단위 일치(기존 F3 self-test 100% 검증).
#
# 펌웨어(FAULT_SIM 빌드) 스트리밍 커맨드:
#   'x'(idx) → g_z1raw 64B   (1024 int32 = 64청크)  결함 응답 z1
#   's'(idx) → g_s1ntt 64B   ( 768 int32 = 48청크)  참 s1(NTT) — 검증용
#   'c'(idx) → g_cpoly 64B   ( 256 int32 = 16청크)  챌린지 c
import struct

Q, QINV, LN = 64513, 940508161, 8192
ZETAS = [0,26964,-16505,22229,30746,20243,19064,-31218,9395,-30985,22859,-8851,32144,13744,21408,17599,-16039,-22946,6241,-19553,10681,22935,22431,-29104,28147,-27527,-29133,-20035,20143,-11361,30820,25252,-22562,-6789,-10049,9383,16304,-12296,16446,18239,-1296,-19725,-32076,11782,-17941,29643,-8577,7893,-21464,-19646,-15130,-2391,30608,-23970,-16608,19616,-7941,26533,-19129,27690,7597,-11459,10615,-9430,11591,7814,12697,32114,-3761,-9604,19813,20353,17456,-16267,-19555,598,-29942,4538,835,15546,3970,-27685,1488,8311,-12442,31352,-17631,1806,-5342,9790,29068,16507,-29051,22131,6759,15510,-14941,28710,1160,-31327,24985,11261,-10623,-27727,21502,18731,-16186,-4127,-18832,12050,-14501,7929,29563,-31064,5913,5322,-16405,2844,29439,5876,-9522,-18586,-9874,23844,30362,-21442,9560,17671,-27989,3350,787,-13857,1657,-21224,-7374,-9190,2464,25555,-3529,-28772,16588,-15739,23475,13666,5764,30980,13633,-7401,-30317,28847,7682,-11808,-8796,14864,-24162,-19194,689,-1311,-31332,-16319,1025,10971,-23016,-2648,-21900,-12543,-25921,28254,28521,-16160,12380,-12882,-30332,-16630,23439,7742,17182,17494,5920,13642,7382,-18166,21422,-30274,-28190,13283,-20316,-9939,10672,21454,6080,-17374,-29735,-25912,-10170,3808,10639,-26985,-10865,25636,17261,-26851,-8253,-3304,18282,-2202,-31368,-22243,13882,12069,-11242,-7729,-10226,1761,-27298,-4800,-17737,-22805,-3528,65,10770,8908,-23751,26934,21921,-27010,-21944,8889,-1035,23224,-9488,-5823,-994,-20206,7655,-16251,-22820,-27740,15822,23078,13803,-8099,2931,9217,-21126,-14203,25492,-12831,7947,17463,-12979,29003,31612,26554,8241,-20175]

def _s32(x):
    x &= 0xFFFFFFFF
    return x - 2**32 if x >= 2**31 else x
def mont_reduce(a):                 # a·2^-32 mod q (레퍼런스 montgomery_reduce 동일)
    t = _s32(_s32(a) * QINV)
    return (a - t * Q) >> 32
def ntt(a):                         # forward NTT (ntt.c 동일)
    a = a[:]; k = 0; ln = 128
    while ln > 0:
        start = 0
        while start < 256:
            k += 1; z = ZETAS[k]
            for j in range(start, start + ln):
                t = mont_reduce(z * a[j + ln]); a[j + ln] = a[j] - t; a[j] = a[j] + t
            start = j + ln + 1
        ln >>= 1
    return a
def _modq(x):
    x %= Q
    return x + Q if x < 0 else x
def _inv(a):
    return pow(_modq(a), Q - 2, Q) if _modq(a) else 0

def _stream(target, cmd, nchunks, timeout=8000):
    buf = bytearray()
    for idx in range(nchunks):
        target.flush(); target.simpleserial_write(cmd, bytes([idx]))
        r = target.simpleserial_read('r', 64, timeout=timeout)
        if not r:
            raise RuntimeError("'%s' chunk %d 무응답 (FAULT_SIM 빌드인지 확인)" % (cmd, idx))
        buf += bytes(r)
    return bytes(buf)

def read_z1raw(target):  return list(struct.unpack('<1024i', _stream(target, 'x', 64)))
def read_s1ntt(target):  return list(struct.unpack('<768i',  _stream(target, 's', 48)))
def read_cpoly(target):  return list(struct.unpack('<256i',  _stream(target, 'c', 16)))

def recover_s1_from_z1(z1, c):
    """z1: 1024 int32(vec0..3, T2 결함 응답=LN*cs1). c: 256 int32(챌린지).
    반환: clean_T2(vec0==±LN*c 여부), s1ntt(복원된 3블록 NTT, 부호 미정)."""
    chat = ntt(c[:]); chatinv = [_inv(v) for v in chat]
    v0 = z1[0:256]
    clean = all(v0[k] == LN * c[k] for k in range(256)) or \
            all(v0[k] == -LN * c[k] for k in range(256))
    rec = []
    for i in range(3):                                   # vec1..3 = 비밀 보유 블록
        blk = z1[(i + 1) * 256:(i + 2) * 256]
        X = ntt([blk[k] // LN for k in range(256)])      # = (-1)^b ĉ∘ŝ1
        rec.append([(_modq(X[k]) * chatinv[k]) % Q for k in range(256)])  # = (-1)^b ŝ1
    return {'clean_T2': clean, 's1ntt': rec}

def agreement(rec_s1, true_s1ntt):
    """복원 s1 vs 디바이스 참 s1(NTT) 일치율. 부호 (-1)^b 는 ±양쪽 비교로 흡수."""
    def agree(sgn):
        a = 0
        for i in range(3):
            for k in range(256):
                if (sgn * rec_s1[i][k]) % Q == _modq(true_s1ntt[i * 256 + k]): a += 1
        return a
    ap, an = agree(1), agree(-1)
    return max(ap, an) / 768.0, ('+' if ap >= an else '-')

def attack_recover(target):
    """디바이스에서 z1·s1·c 를 받아 직접 추출 → (일치율, 부호, clean_T2)."""
    z1 = read_z1raw(target); s1 = read_s1ntt(target); c = read_cpoly(target)
    r = recover_s1_from_z1(z1, c)
    rate, sgn = agreement(r['s1ntt'], s1)
    return {'agreement': rate, 'sign': sgn, 'clean_T2': r['clean_T2']}
