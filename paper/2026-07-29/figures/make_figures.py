# -*- coding: utf-8 -*-
# HAETAE-IRV 논문 그림 생성 — 표 A(커버리지)·B(2차결함)·C(비용).
# 실행: (cwenv 등 matplotlib 있는 환경에서)  python make_figures.py
# 출력: fig_coverage.{pdf,png}, fig_2ndorder.{pdf,png}, fig_cost.{pdf,png}  (현재 폴더)
# 데이터는 test/2026-06-30/*.csv 의 실측 결과를 내장(자체완결).
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

VARIANTS = ['baseline', 'double', 'leeha', 'irv']
FAULTS   = ['SEED', 'SIGNBIT', 'UNPACK', 'LSB', 'CS (T1)', 'ADDY (T2)', 'REJECT (RB)']

# 커버리지: 'L'=LEAK(미차단), 'B'=blocked(차단)   (행=fault, 열=variant)
COV = {
    'baseline': ['L','L','L','L','L','L','L'],
    'double':   ['B','B','B','B','B','B','B'],
    'leeha':    ['B','B','B','B','B','B','L'],   # REJECT만 LEAK
    'irv':      ['B','B','B','B','B','B','B'],
}
# 2차결함(T2 + 검사분기 스킵): 'L'=우회(누설), 'B'=차단
SECOND = {'baseline':'L', 'double':'L', 'leeha':'L', 'irv':'B'}
# 비용
TIME_REL = {'baseline':1.000, 'double':2.000, 'leeha':1.137, 'irv':1.140}
CODE_OVH = {'baseline':0.0,   'double':0.7,   'leeha':25.4,  'irv':26.3}   # text % 증가

RED, GREEN = '#d9534f', '#5cb85c'
COL = {'L': RED, 'B': GREEN}

def fig_coverage():
    # 흑백(그레이스케일): blocked=흰색, LEAK=회색+빗금. 단 글자 자리는 흰 박스를 깔아 빗금 제거(가독성).
    fig, ax = plt.subplots(figsize=(6.2, 4.2), dpi=150)
    txt_bbox = dict(facecolor='white', edgecolor='none', boxstyle='square,pad=0.15')
    for i in range(len(FAULTS)):
        for j, v in enumerate(VARIANTS):
            leak = (COV[v][i] == 'L')
            ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, facecolor=('0.80' if leak else 'white'),
                                       edgecolor='black', lw=0.8, hatch=('////' if leak else None)))
            ax.text(j, i, 'LEAK' if leak else 'blk', ha='center', va='center',
                    color='black', fontsize=8, fontweight=('bold' if leak else 'normal'),
                    bbox=(txt_bbox if leak else None))
    ax.set_xlim(-0.5, len(VARIANTS)-0.5); ax.set_ylim(len(FAULTS)-0.5, -0.5)
    ax.set_xticks(range(len(VARIANTS))); ax.set_xticklabels(VARIANTS)
    ax.set_yticks(range(len(FAULTS)));   ax.set_yticklabels(FAULTS)
    ax.set_title('Coverage: blocked vs leaked')
    ax.legend(handles=[Patch(facecolor='white', edgecolor='black', label='blocked'),
                       Patch(facecolor='0.80', edgecolor='black', hatch='////', label='LEAK')],
              loc='upper left', bbox_to_anchor=(1.01, 1.0))
    fig.tight_layout()
    for ext in ('pdf','png'): fig.savefig('fig_coverage.'+ext, bbox_inches='tight')
    plt.close(fig)

def fig_2ndorder():
    fig, ax = plt.subplots(figsize=(5.0, 3.2), dpi=150)
    vals = [1 if SECOND[v]=='B' else 0 for v in VARIANTS]   # 1=blocked, 0=leak
    colors = [GREEN if v==1 else RED for v in vals]
    ax.bar(VARIANTS, [1]*len(VARIANTS), color=colors)
    for j, v in enumerate(VARIANTS):
        ax.text(j, 0.5, 'blocked' if SECOND[v]=='B' else 'LEAK\n(bypassed)',
                ha='center', va='center', color='white', fontsize=9, fontweight='bold')
    ax.set_yticks([]); ax.set_ylim(0,1)
    ax.set_title('2nd-order fault (T2 + skip detection branch)')
    ax.legend(handles=[Patch(color=GREEN, label='blocked (IRV: branchless infective)'),
                       Patch(color=RED, label='bypassed (detect-and-abort)')],
              loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=1, fontsize=8)
    fig.tight_layout()
    for ext in ('pdf','png'): fig.savefig('fig_2ndorder.'+ext, bbox_inches='tight')
    plt.close(fig)

def fig_cost():
    fig, ax1 = plt.subplots(figsize=(5.6, 3.4), dpi=150)
    x = np.arange(len(VARIANTS)); w = 0.38
    t = [TIME_REL[v] for v in VARIANTS]; c = [CODE_OVH[v] for v in VARIANTS]
    b1 = ax1.bar(x - w/2, t, w, color='#337ab7', label='sign time (relative)')
    ax1.set_ylabel('sign time (x baseline)'); ax1.set_ylim(0, 2.3)
    ax1.axhline(1.0, ls=':', color='gray', lw=0.8)
    for j, val in enumerate(t): ax1.text(x[j]-w/2, val+0.03, '%.2fx'%val, ha='center', fontsize=8)
    ax2 = ax1.twinx()
    b2 = ax2.bar(x + w/2, c, w, color='#f0ad4e', label='code overhead (%)')
    ax2.set_ylabel('code (text) overhead (%)'); ax2.set_ylim(0, 32)
    for j, val in enumerate(c): ax2.text(x[j]+w/2, val+0.4, '%.1f%%'%val, ha='center', fontsize=8)
    ax1.set_xticks(x); ax1.set_xticklabels(VARIANTS)
    ax1.set_title('Cost: sign time and code overhead')
    ax1.legend(handles=[b1, b2], loc='upper left', fontsize=8)
    fig.tight_layout()
    for ext in ('pdf','png'): fig.savefig('fig_cost.'+ext, bbox_inches='tight')
    plt.close(fig)

if __name__ == '__main__':
    fig_coverage(); fig_2ndorder(); fig_cost()
    print('saved: fig_coverage / fig_2ndorder / fig_cost  (.pdf + .png)')
