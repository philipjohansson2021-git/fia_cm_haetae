#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAETAE 결함주입 대응기법 커버리지/오버헤드 시뮬레이터 (논리 연산 수준, 아키텍처 독립)

- 대응기법: baseline, double_comp(전체 2회 비교), Lee-Ha 4종(verify/partial_double/sanity/seed_in_loop),
            Lee-Ha 통합(suite), HAETAE-IRV
- 결함모델: skip, register, bitflip, byteflip, zeroing, set_const, loop_abort
- 공격점(서명 연산 라인): 두 논문(우리/Lee-Ha)의 공격지점을 망라
- 출력: (1) 공격점x결함모델 leak 여부  (2) 대응기법별 커버리지  (3) 결함모델별 커버리지
        (4) 상대 오버헤드. 결과를 CSV/표로 출력 -> 별도 스크립트가 MD로 정리.

주의: 각 (공격점,결함모델)의 'leak 여부'와 대응기법 '탐지 여부'는 두 논문의 공격/대응
      메커니즘에서 도출한 '결함효과 규칙'으로 결정한다(아래 each rule에 근거 주석).
      이는 커버리지 비교를 위한 논리 모델이며, 절대 오버헤드는 STM32F4 실측으로 대체한다.
"""
import itertools, csv, json

FAULTS = ["skip","register","bitflip","byteflip","zeroing","set_const","loop_abort"]

# 공격점(서명 라인). 각 항목: (id, 설명, 출처)
ATTACK_POINTS = [
    ("seed_gen",   "샘플링 시드 생성(K||mu->seed)", "LeeHa"),
    ("expandY",    "난수 y 확장(expandYbb)",        "LeeHa/우리(LA)"),
    ("sign_bit",   "bimodal 부호비트 b",            "LeeHa"),
    ("unpackA",    "공개행렬 A 언패킹",             "LeeHa"),
    ("commit_Ay",  "A*y, HighBits(commit w)",       "공통"),
    ("lsb",        "LSB(round(y0)) 처리",           "LeeHa"),
    ("challenge",  "챌린지 c 계산",                 "공통"),
    ("cs1_mul",    "c*s1 곱셈 (T1)",                "우리(T1)"),
    ("cs2_mul",    "c*s2 곱셈",                     "공통"),
    ("add_y",      "z = LN*cs1 + y  의 +y (T2)",    "우리(T2)"),
    ("reject_B1",  "거부 샘플링 판정(B1)",          "우리(RB)"),
    ("hint",       "힌트 생성",                     "공통"),
    ("encode",     "서명 인코딩",                   "공통"),
    ("key_mem",    "비밀키 메모리(영속 변조)",      "공통"),
]

# ---- 1) baseline에서 (공격점,결함모델)이 '키유출(leak)'을 유발하는가? ----
# leak_type: 'single'(단일트레이스 직접복원) / 'diff'(다중서명 차분) / 'stat'(통계적 누설)
#            / None(안전: 무해하거나 자연 거부/무효서명/크래시)
def baseline_leak(point, fault):
    p=point
    # 시드: skip/zeroing/set_const 으로 시드를 예측가능 고정 -> 예측y -> 키복구 (LeeHa seed)
    if p=="seed_gen":
        return "single" if fault in ("skip","zeroing","set_const") else (
               "stat" if fault in ("register","bitflip","byteflip") else None)
    # y 확장: loop_abort -> 저엔트로피 y -> 누설(LA, Espitau). skip/zeroing -> y=0 -> 강한 누설
    if p=="expandY":
        return "single" if fault in ("zeroing","skip") else (
               "stat" if fault in ("loop_abort","register","set_const") else
               "stat" if fault=="bitflip" else "stat" if fault=="byteflip" else None)
    # 부호비트 b: 반전/고정 -> 단일서명만으론 유효서명, 정상+오류 2서명 차분으로 복구(LeeHa) => diff
    if p=="sign_bit":
        return "diff" if fault in ("bitflip","register","set_const","skip","zeroing") else "diff"
    # A 언패킹: 잘못된 A -> 잘못된 c -> 정상/오류 차분 복구(LeeHa) => diff
    if p=="unpackA":
        return "diff" if fault in ("skip","register","bitflip","byteflip","zeroing","set_const") else "stat"
    # commit(A*y) 변조: 잘못된 c -> 차분 복구 가능
    if p=="commit_Ay":
        return "diff" if fault in ("register","bitflip","byteflip","set_const","zeroing","skip") else "stat"
    # LSB 처리: 다른 c 샘플 -> 정상/오류 차분 복구(LeeHa LSB) => diff
    if p=="lsb":
        return "diff" if fault in ("skip","register","bitflip","byteflip","zeroing","set_const") else "stat"
    # 챌린지 c 변조: 잘못된 c -> 차분
    if p=="challenge":
        return "diff" if fault in ("register","bitflip","byteflip","set_const","zeroing") else (
               "diff" if fault=="skip" else "stat")
    # c*s1 스킵(T1): z≈y -> nonce 누설(우리 T1). skip/zeroing 강함
    if p=="cs1_mul":
        return "single" if fault in ("skip","zeroing") else "stat"
    if p=="cs2_mul":
        # cs2는 commit/hint쪽 -> 변조시 검증불일치(무효) 또는 약한 누설
        return "stat" if fault in ("skip","zeroing","register") else None
    # +y 스킵(T2): z=LN*cs1 -> 단일트레이스 직접 s1 복원(우리 T2). skip/zeroing 강함
    if p=="add_y":
        return "single" if fault in ("skip","zeroing") else (
               "stat" if fault in ("register","bitflip","byteflip","set_const") else None)
    # 거부판정 스킵: 경계초과 z 방출 -> 통계적 누설(RB)
    if p=="reject_B1":
        return "stat" if fault in ("skip","register","set_const","bitflip","zeroing") else None
    # 힌트/인코딩: 대개 무효서명(안전) 또는 DoS
    if p in ("hint","encode"):
        return None
    # 비밀키 메모리 영속 변조: 잘못된 키로 서명 -> 일부 누설 가능
    if p=="key_mem":
        return "stat" if fault in ("register","bitflip","byteflip","set_const","zeroing") else None
    return None

# ---- 2) 각 대응기법이 해당 leak을 탐지/무효화하는가? ----
# 규칙 근거를 주석으로 명시.
def detect(cm, point, fault, leak):
    if leak is None:
        return None  # leak 아님 -> 평가 제외
    p=point

    if cm=="baseline":
        return False

    if cm=="double_comp":
        # 전체 서명 2회 비교: 결함이 한 실행에만 영향(일시적)이면 두 출력 상이 -> 탐지.
        # 단, 영속 입력 변조(key_mem)나 결정론적으로 두 실행 모두 동일하게 발생하는 결함은 미탐.
        if p=="key_mem":            # 두 실행 모두 같은 잘못된 키 -> 동일 출력 -> 미탐
            return False
        if p=="seed_gen" and fault in ("zeroing","set_const"):
            # 시드가 결정론적으로 동일 고정 -> 두 실행 동일 -> 미탐
            return False
        return True

    if cm=="leeha_verify":   # 서명후검증(B2 검증 1회)
        # 잘못된 c/공개경로(LSB,unpackA,commit,challenge) -> 검증 c'!=c 또는 노름>B2 -> 탐지.
        # 미탐: 부호비트(유효서명), 시드(유효서명), 거부우회 RB(노름<B2 통과). 우리 T1/T2도
        #       힌트보정으로 검증 통과할 수 있어 미탐(논문 근거: verify 경계 B2가 느슨).
        if p in ("lsb","unpackA","commit_Ay","challenge"):
            return True
        return False

    if cm=="leeha_partial_double":  # 시드생성+부호비트 경로만 이중연산 비교
        # 탐지: seed_gen, sign_bit, expandY(시드기반). 미탐: 그 외(LSB,unpackA,c,cs,add_y,reject,key).
        return p in ("seed_gen","sign_bit","expandY")

    if cm=="leeha_sanity":   # XOF 버퍼 all-zero/all-same 검사
        # 탐지: 시드/난수 버퍼가 0 또는 동일패턴이 되는 결함(seed zeroing/skip, expandY zeroing/skip)
        if p=="seed_gen" and fault in ("skip","zeroing","set_const"):
            return True
        if p=="expandY" and fault in ("skip","zeroing"):
            return True
        return False

    if cm=="leeha_seed_in_loop":   # 시드를 거부루프 내부로 이동(단일 시드고정 무력화)
        if p=="seed_gen" and fault in ("skip","zeroing","set_const"):
            return True
        return False

    if cm=="leeha_suite":    # Lee-Ha 4종 통합 (위 4개 중 하나라도 탐지하면 탐지)
        return any(detect(c,point,fault,leak) for c in
                   ("leeha_verify","leeha_partial_double","leeha_sanity","leeha_seed_in_loop"))

    if cm=="irv":
        # M1: c*s 전체 재계산 비교 -> z관련 결함(cs1,cs2,add_y, c, commit, challenge 의 z영향) 탐지
        # M2: 서명경계 B1 재검사 -> 거부우회(reject_B1) 탐지
        # M3: 비밀키 체크섬 -> key_mem 탐지
        # M4: 무분기 감염 -> 검사-스킵 이차결함 내성(단일결함 모델 내 항상 유효)
        # 미탐(단일결함): sign_bit(동일 b로 재계산되면 일치, 단 단일트레이스 누설 아님=diff),
        #               seed_gen/expandY 중 'z 관계는 유지되며 y 자체가 약한' 경우는 부분 탐지.
        if p in ("cs1_mul","cs2_mul","add_y","challenge","commit_Ay","lsb","unpackA"):
            return True   # z = y+(-1)^b c s1 재계산 불일치로 탐지
        if p=="reject_B1":
            return True   # M2
        if p=="key_mem":
            return True   # M3
        if p=="expandY":
            return True   # 재계산시 z 불일치(잘못된 y가 z에 반영) -> 탐지
        if p=="seed_gen":
            # 시드고정으로 예측가능 y가 나와도 z=y+cs1 관계 자체는 성립 -> M1 미탐.
            # 단 M2/M3 무관. => 부분 미탐 (정직하게 False)
            return False
        if p=="sign_bit":
            return False  # 동일 b 재계산 -> 일치(단, 단일결함으론 직접 누설 아님)
        return False
    raise ValueError(cm)

CMS = ["baseline","double_comp","leeha_verify","leeha_partial_double",
       "leeha_sanity","leeha_seed_in_loop","leeha_suite","irv"]

# ---- 시뮬레이션 실행 ----
rows=[]   # (point, fault, leak_type, {cm:detected})
for (pid,desc,src) in ATTACK_POINTS:
    for f in FAULTS:
        leak=baseline_leak(pid,f)
        det={cm:detect(cm,pid,f,leak) for cm in CMS}
        rows.append((pid,desc,src,f,leak,det))

# 커버리지 집계: 분모 = leak!=None 인 케이스 수
def coverage(cm, fault_filter=None, leak_filter=None):
    tot=det=0
    for (pid,desc,src,f,leak,d) in rows:
        if leak is None: continue
        if fault_filter and f!=fault_filter: continue
        if leak_filter and leak!=leak_filter: continue
        tot+=1
        if d[cm]: det+=1
    return det,tot

print("=== 전체 커버리지 (leak 케이스 중 탐지 비율) ===")
overall={}
for cm in CMS:
    d,t=coverage(cm); overall[cm]=(d,t)
    print(f"  {cm:22s}: {d:3d}/{t:3d} = {100*d/t:5.1f}%")

print("\n=== 결함모델별 커버리지 (%) ===")
hdr="point/cm".ljust(0)
print("fault".ljust(12)+"".join(f"{cm[:10]:>12s}" for cm in CMS if cm!="baseline"))
permodel={}
for f in FAULTS:
    line=f"{f:12s}"
    permodel[f]={}
    for cm in CMS:
        if cm=="baseline": continue
        d,t=coverage(cm,fault_filter=f)
        permodel[f][cm]=(d,t)
        line+=f"{(100*d/t if t else 0):11.0f}%"
    print(line)

print("\n=== leak 유형별 케이스 수 ===")
from collections import Counter
lc=Counter(leak for *_,leak,_ in rows if leak)
print("  ", dict(lc))

# ---- 상대 오버헤드 (연산횟수 배수, 아키텍처 독립 추정) ----
# 기준: 1회 서명 = 1.00. 추가 연산을 서명비용 대비 배수로.
# (절대 사이클/RAM/코드는 STM32F4 실측으로 대체 — 여기선 상대 비교용)
OVERHEAD = {
 "baseline":            {"time":1.00,"note":"기준"},
 "double_comp":         {"time":2.00,"note":"전체 서명 2회"},
 "leeha_verify":        {"time":1.05,"note":"검증 1회 추가(검증<<서명)"},
 "leeha_partial_double":{"time":1.01,"note":"시드+부호 경로만 재계산"},
 "leeha_sanity":        {"time":1.001,"note":"버퍼 패턴검사(상수)"},
 "leeha_seed_in_loop":  {"time":1.002,"note":"시드생성 위치이동(리젝션시 추가)"},
 "leeha_suite":         {"time":1.06,"note":"위 4종 합산(대략)"},
 "irv":                 {"time":1.03,"note":"c*s 1회 재계산+노름+체크섬+무분기마스킹"},
}
print("\n=== 상대 오버헤드(서명비용 배수) ===")
for cm in CMS:
    print(f"  {cm:22s}: x{OVERHEAD[cm]['time']:.3f}  ({OVERHEAD[cm]['note']})")

# CSV 저장 (상세)
with open("coverage_detail.csv","w",newline="") as fp:
    w=csv.writer(fp); w.writerow(["point","desc","source","fault","leak_type"]+CMS)
    for (pid,desc,src,f,leak,d) in rows:
        w.writerow([pid,desc,src,f,leak or "-"]+[("" if leak is None else ("Y" if d[cm] else "N")) for cm in CMS])
json.dump({"overall":{k:list(v) for k,v in overall.items()},
           "permodel":{f:{cm:list(v) for cm,v in permodel[f].items()} for f in FAULTS},
           "overhead":OVERHEAD,"cms":CMS,"faults":FAULTS},
          open("coverage_summary.json","w"),ensure_ascii=False,indent=1)
print("\nsaved coverage_detail.csv, coverage_summary.json")
