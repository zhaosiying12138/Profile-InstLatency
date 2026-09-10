#!/usr/bin/env python3
"""Print the E7 36-pair mixed-stream verdict matrix (slope per pair @m1)."""
import glob, json
from collections import defaultdict

mix = defaultdict(list)
for f in sorted(glob.glob('experiments/e07-*-m1-*/trace.json')):
    t = json.load(open(f)); m = t['meta']; e = t['entries']
    if any(x['cycle'] is None for x in e):
        continue
    mix[(m['a'], m['b'])].append((m['pairs'], e[-1]['cycle'] - e[0]['cycle']))
INS = ["vadd_vv", "vmul_vv", "vdivu_vv", "vmseq_vv",
       "vredsum_vs", "vslideup_vx", "vcpop_m", "viota_m"]
R = {'vadd_vv': 1, 'vmul_vv': 1, 'vdivu_vv': 12, 'vmseq_vv': 4,
     'vredsum_vs': 2, 'vslideup_vx': 4, 'vcpop_m': 1, 'viota_m': 1}
print(f"{'':>8}" + "".join(f"{c[:7]:>9}" for c in INS))
for a in INS:
    row = f"{a[:7]:>8}"
    for b in INS:
        v = mix.get((a, b))
        if not v:
            row += f"{'-':>9}"; continue
        p, d = v[0]
        slope = d / p
        par = slope <= max(R[a], R[b]) + 0.5
        ser = slope >= R[a] + R[b] - 0.5
        tag = 'P' if par and not ser else ('S' if ser else 'm')
        row += f"{slope:>7.1f}{tag}"
    print(row)
print("\nP=parallel(max R)  S=serial(Ra+Rb)  m=partial")
