#!/usr/bin/env python3
"""Redraw the two chapter-5.2 overview figures as PNGs (matplotlib Agg).

stream_nscan.png       E2 N-scan: measured marker deltas vs N, with the fitted
                       delta = R*N - mu line per representative (instr, LMUL).
design_vs_measured.png design R vs measured R per instruction per LMUL;
                       divergent (emergent) instructions highlighted.

Data source: experiments/e02-*/trace.json + results/profile_measured.json
(design values inlined from config/yushuxin_timing_v2.yaml via yxmodel).
"""
import json, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

# matplotlib cannot use .ttc collections for CJK reliably: register the
# extracted SC face once (see repo docs / make_figs history).
_CJK_TTF = os.path.expanduser('~/.local/share/fonts/NotoSansCJK-SC-extracted.ttf')
if os.path.exists(_CJK_TTF):
    font_manager.fontManager.addfont(_CJK_TTF)
    plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'DejaVu Sans']
else:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'results', 'shots')

plt.rcParams['axes.unicode_minus'] = False

# --------------------------------------------------------------- data helpers
def stream_deltas(instr, lmul, ns=(2, 3, 4, 6, 8, 12)):
    pts = {}
    for n in ns:
        p = os.path.join(ROOT, 'experiments', f'e02-{instr}-{lmul}-n{n}', 'trace.json')
        if os.path.exists(p):
            e = json.load(open(p))['entries']
            pts[n] = e[-1]['cycle'] - e[0]['cycle']
    return pts

sys.path.insert(0, HERE)
from yxmodel import TimingModel
m = TimingModel(os.path.join(ROOT, 'config', 'yushuxin_timing_v2.yaml'))

INSTRS = ['vadd_vv', 'vmul_vv', 'vdivu_vv', 'vmseq_vv',
          'vredsum_vs', 'vslideup_vx', 'vcpop_m', 'viota_m']
LABEL = {'vadd_vv': 'vadd', 'vmul_vv': 'vmul', 'vdivu_vv': 'vdivu', 'vmseq_vv': 'vmseq',
         'vredsum_vs': 'vredsum', 'vslideup_vx': 'vslideup', 'vcpop_m': 'vcpop', 'viota_m': 'viota'}

# ------------------------------------------------------------------ fig 1
SERIES = [  # (instr, lmul, color): slope R and the delta=N*R-mu line are drawn
    ('vadd_vv',    'm1', '#2c7fb8'),
    ('vmul_vv',    'm4', '#41ab5d'),
    ('vredsum_vs', 'm2', '#88419d'),
    ('vdivu_vv',   'm1', '#d7301f'),
]
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
for instr, lm, c in SERIES:
    pts = stream_deltas(instr, lm)
    xs = sorted(pts)
    R = m.R(instr, lm)
    mu = m.mu(instr) if not m.is_nonpipelined(instr) else m.opLat(instr)
    # measured R from slope for annotation honesty (matches design here)
    fit = [R * n - mu for n in xs]
    ax.scatter(xs, [pts[x] for x in xs], color=c, s=26, zorder=3)
    ax.plot(xs, fit, color=c, lw=1.4,
            label=f'{LABEL[instr]} {lm}: slope R={R}')
ax.set_yscale('log')
ax.set_xticks((2, 3, 4, 6, 8, 12))
ax.set_xlabel('独立流长度 N（E2 目的寄存器轮转）')
ax.set_ylabel('marker Δ（周期，log 轴）')
ax.set_title('E2 独立流 N 扫描：Δ = R·N − μ，斜率即吞吐 R')
ax.grid(True, which='both', alpha=.28, lw=.6)
ax.legend(fontsize=8.5, loc='upper left')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'stream_nscan.png'))
plt.close(fig)

# ------------------------------------------------------------------ fig 2
meas = json.load(open(os.path.join(ROOT, 'results', 'profile_measured.json')))['profile']
LMULS = [('m1', 1.0), ('m2', 2.6), ('m4', 4.2)]      # x offsets inside a group
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
for i, instr in enumerate(INSTRS):
    diverged = False
    for lm, dx in LMULS:
        d, v = m.R(instr, lm), meas[instr]['R'][lm]
        if d != v:
            diverged = True
        x = i + dx
        ax.plot([x, x], [d, v], color='#d7301f' if d != v else '#999999',
                lw=2.2 if d != v else 1.2, zorder=2)
        ax.scatter([x], [d], facecolors='white', edgecolors='#555', s=30, zorder=3)
        ax.scatter([x], [v], color='#7a0177', s=30, zorder=3)
    if diverged:
        ax.annotate('涌现', (i + 2.6, max(m.R(instr, 'm4'), meas[instr]['R']['m4'])),
                    xytext=(0, 7), textcoords='offset points', ha='center',
                    fontsize=8.5, color='#d7301f', fontweight='bold')
ax.set_xticks(range(len(INSTRS)))
ax.set_xticklabels([LABEL[k] for k in INSTRS])
ax.set_ylabel('宏吞吐 R（周期/条）')
ax.set_title('设计 R（空心 ○） vs 实测 R（实心 ●）：四类涌现分叉（红线）')
ax.set_yscale('log')
ax.grid(True, axis='y', which='both', alpha=.28, lw=.6)
from matplotlib.lines import Line2D
ax.legend(handles=[
    Line2D([], [], marker='o', ls='', mfc='white', mec='#555', label='设计 R（真值表）'),
    Line2D([], [], marker='o', ls='', color='#7a0177', label='实测 R（E2 反演）'),
    Line2D([], [], color='#d7301f', lw=2.2, label='分差 = 涌现（按实测落表）'),
], fontsize=8.5, loc='upper left')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'design_vs_measured.png'))
plt.close(fig)
print('wrote stream_nscan.png & design_vs_measured.png ->', OUT)
