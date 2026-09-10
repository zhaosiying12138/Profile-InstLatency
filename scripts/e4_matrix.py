#!/usr/bin/env python3
"""Print the E4 cross-class RAW matrix (dep - ctrl) at m1 from real traces."""
import glob, json, sys
from collections import defaultdict

k0 = defaultdict(dict)
for f in sorted(glob.glob('experiments/e04-*-m1-k0-*/trace.json')):
    t = json.load(open(f)); m = t['meta']; e = t['entries']
    if any(x['cycle'] is None for x in e):
        continue
    k0[(m['producer'], m['consumer'])]['ctrl' if m['control'] else 'dep'] = \
        e[-1]['cycle'] - e[0]['cycle']
INS = ["vadd_vv", "vmul_vv", "vdivu_vv", "vmseq_vv",
       "vredsum_vs", "vslideup_vx", "vcpop_m", "viota_m"]
print("        " + "".join(f"{c[:7]:>9}" for c in INS))
for p in INS:
    row = f"{p[:7]:>8}"
    for c in INS:
        v = k0.get((p, c), {})
        row += f"{(v['dep']-v.get('ctrl',1)):>9}" if 'dep' in v else f"{'-':>9}"
    print(row)
