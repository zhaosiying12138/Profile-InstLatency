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

# ------------------------------------------------------------------ fig 3
# latency_m1: chain (E3) covers the four self-chainable instructions, the
# E4 matrix covers the four non-chainable ones; the mu-op design formula is
# the extrapolation they are checked against (7/8 converge; vmseq diverges).
CHAIN_L1 = {'vadd_vv': 3, 'vmul_vv': 4, 'vdivu_vv': 12, 'vredsum_vs': 6}
# E4-sourced L@lambda=1 for the NON-chainable classes only (evidence files
# e04-vmseq_vv-x-*, e04-vslideup_vx-*, e04-vcpop_m-x-*, e04-viota_m-*).
# vdivu's E4 cells are writeback-alignment anomalous (blog footnote) and are
# NOT plotted as matrix points -- its L is chain-sourced.
MATRIX_L1 = {'vmseq_vv': 5, 'vslideup_vx': 4, 'vcpop_m': 3, 'viota_m': 5}
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
xs = range(len(INSTRS))
muop = [m.L(i, 'm1') for i in INSTRS]            # design formula
ax.scatter(xs, muop, marker='o', facecolors='white', edgecolors='#4a148c',
           s=46, label='μop 外推：L_micro+(λ−1)μ（设计）', zorder=3)
cx = [i for i, k in enumerate(INSTRS) if k in CHAIN_L1]
ax.scatter(cx, [CHAIN_L1[k] for k in INSTRS if k in CHAIN_L1], marker='s',
           color='#08519c', s=40, label='链（E3 实测，可自链 4 条）', zorder=4)
mx = [i for i, k in enumerate(INSTRS) if k in MATRIX_L1]
ax.scatter(mx, [MATRIX_L1[k] for k in INSTRS if k in MATRIX_L1], marker='D',
           color='#d7301f', s=34, label='矩阵（E4 实测，不可自链 4 条）', zorder=4)
i_vm = INSTRS.index('vmseq_vv')
ax.annotate('vmseq：设计 2 → 实测 5\n（vmask_mv 伴随涌现）',
            (i_vm, 5), xytext=(i_vm + 0.9, 9.2), fontsize=8.5, color='#d7301f',
            arrowprops=dict(arrowstyle='->', color='#d7301f', lw=1))
ax.set_xticks(list(xs))
ax.set_xticklabels([LABEL[k] for k in INSTRS])
ax.set_ylabel('L@λ=1（周期）')
ax.set_title('L(m1) 两路合围（E3 链 + E4 矩阵）对照 μop 设计外推：7/8 会合，vmseq 分叉')
ax.set_ylim(0, 14)
ax.grid(True, axis='y', alpha=.28, lw=.6)
ax.legend(fontsize=8.5, loc='upper left')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'latency_m1.png'))
plt.close(fig)

# ------------------------------------------------------------------ fig 4
# matrix_heat: normalized E4 RAW matrix, consumers (y) x producers (x).
import glob
from collections import defaultdict
k0 = defaultdict(dict)
for f in sorted(glob.glob(os.path.join(ROOT, 'experiments/e04-*-m1-k0-*', 'trace.json'))):
    t = json.load(open(f)); meta = t['meta']; e = t['entries']
    if any(x['cycle'] is None for x in e):
        continue
    k0[(meta['producer'], meta['consumer'])]['ctrl' if meta['control'] else 'dep'] = \
        e[-1]['cycle'] - e[0]['cycle']
raw = {}
for (p, c), v in k0.items():
    if 'dep' in v:
        raw[(p, c)] = v['dep'] - v.get('ctrl', 1)
CONS = [i for i in INSTRS]                       # y: consumers
norm = [[(raw[(p, c)] - raw[('vcpop_m', c)]) if (p, c) in raw and ('vcpop_m', c) in raw
         else float('nan') for p in INSTRS] for c in CONS]
import numpy as np
mat = np.array(norm, dtype=float)
fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=200)
im = ax.imshow(mat, cmap='YlGnBu', aspect='auto')
ax.set_xticks(range(len(INSTRS)))
ax.set_xticklabels([LABEL[k] for k in INSTRS], rotation=30, ha='right')
ax.set_yticks(range(len(CONS)))
ax.set_yticklabels([LABEL[k] for k in CONS])
for yi in range(len(CONS)):
    for xi in range(len(INSTRS)):
        v = mat[yi, xi]
        if np.isnan(v):
            ax.text(xi, yi, '—', ha='center', va='center', color='#999999', fontsize=9)
        else:
            ax.text(xi, yi, f'{v:.0f}', ha='center', va='center', fontsize=8.5,
                    color='white' if v > np.nanmax(mat) * 0.55 else '#222')
ax.set_xlabel('生产者（producer）')
ax.set_ylabel('消费者（consumer）')
ax.set_title('E4 归一化 RAW 矩阵（列基线 = vcpop 行）：同管簇低 / 跨管簇高')
fig.colorbar(im, ax=ax, label='有效 RAW（周期）', shrink=.85)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'matrix_heat.png'))
plt.close(fig)

# ------------------------------------------------------------------ fig 5
# mca_vs_gem5: llvm-mca -resource-pressure (model R) vs gem5 measured R.
import subprocess
LLVM_MCA = '/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca'
out = subprocess.run([LLVM_MCA, '-mtriple=riscv64', '-mcpu=YuShuXinV2',
                      '-resource-pressure',
                      os.path.join(ROOT, 'tests/all_instr_lmuls.s')],
                     capture_output=True, text=True, check=True).stdout
sec = out.split('Resource pressure by instruction:')[1]
mca_R = defaultdict(dict)
cur_lm = None
for line in sec.splitlines():
    if 'vsetvli' in line:
        cur_lm = line.split('e32, ')[1].split(',')[0]
    for k in INSTRS:
        asm_name = {'vadd_vv': 'vadd.vv', 'vmul_vv': 'vmul.vv', 'vdivu_vv': 'vdivu.vv',
                    'vmseq_vv': 'vmseq.vv', 'vredsum_vs': 'vredsum.vs',
                    'vslideup_vx': 'vslideup.vx', 'vcpop_m': 'vcpop.m',
                    'viota_m': 'viota.m'}[k]
        if asm_name + '\t' in line:
            cells = line.split(asm_name)[0].split()
            try:
                v = max(float(c) for c in cells if c not in ('-',))
            except ValueError:
                continue
            mca_R[k][cur_lm] = v
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
for i, k in enumerate(INSTRS):
    for lm, dx in LMULS:
        mv = mca_R[k].get(lm)
        gv = meas[k]['R'][lm]
        if mv is None:
            continue
        x = i + dx
        if mv != gv:
            ax.plot([x, x], [mv, gv], color='#d7301f', lw=2.2, zorder=2)
        ax.scatter([x], [mv], facecolors='white', edgecolors='#555', s=30, zorder=3)
        ax.scatter([x], [gv], color='#7a0177', s=30, zorder=3)
i_io = INSTRS.index('viota_m')
ax.annotate('viota m4：模型 4（保守整数）vs 实测 3（分数 5/2 有界）',
            (i_io + 4.2, 4), xytext=(i_io - 3.4, 12), fontsize=8.5, color='#d7301f',
            arrowprops=dict(arrowstyle='->', color='#d7301f', lw=1))
ax.set_xticks(range(len(INSTRS)))
ax.set_xticklabels([LABEL[k] for k in INSTRS])
ax.set_ylabel('R（周期/条，log 轴）')
ax.set_title('llvm-mca（模型，-resource-pressure） vs gem5 实测：R 逐指令对表')
ax.set_yscale('log')
ax.grid(True, axis='y', which='both', alpha=.28, lw=.6)
ax.legend(handles=[
    Line2D([], [], marker='o', ls='', mfc='white', mec='#555', label='llvm-mca / .td 模型 R'),
    Line2D([], [], marker='o', ls='', color='#7a0177', label='gem5 实测 R（E2 反演）'),
    Line2D([], [], color='#d7301f', lw=2.2, label='分差（viota 保守整数落地）'),
], fontsize=8.5, loc='upper left')
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'mca_vs_gem5.png'))
plt.close(fig)
print('wrote 4 figures ->', OUT)
