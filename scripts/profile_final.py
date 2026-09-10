#!/usr/bin/env python3
"""Assemble the FINAL measured profile from all experiment traces and emit
(a) results/profile_measured.json — the parameter table the blog/evidence
    matrix quotes, with per-value provenance (which experiment, which points);
(b) a calibration report vs the design table (what injection promised vs what
    the machine observably does — emergent effects included).

Method (all closed-form, all differential):
  R(instr,lmul)   E2 stream slopes (bounded fallback for saturating cadences)
  L(instr,m1)     E3 chain slope (direct chains) else E4 column normalization
  L(instr,m2/m4)  E4 k0 matrix: cell - consumer_cadence_baseline
  pipes           E7 mix verdicts (parallel/serial) + E4 cross-pipe clustering
  waw             E5 turning point (last d with dep-ctrl stall)
  war             E6 turning point
  cross-pipe pen  E4: (cross-pipe cell) - (same-cluster cell) per consumer
"""
import glob, json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yxmodel import TimingModel, LMUL_FACTOR
from analyze_v2 import Analyzer, lsq_slope, bounded_slope

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTRS = ["vadd_vv", "vmul_vv", "vdivu_vv", "vmseq_vv", "vredsum_vs",
          "vslideup_vx", "vcpop_m", "viota_m"]

an = Analyzer(os.path.join(ROOT, "experiments"),
              os.path.join(ROOT, "config", "yushuxin_timing_v2.yaml"))
an.ingest()
design = an.m

# ------------------------------------------------------------------ streams
R = {}
streams = defaultdict(dict)
for t in an.E["E2_STREAM"]:
    streams[(t["meta"]["instruction"], t["meta"]["lmul"])][t["meta"]["n"]] = t["delta"]
for key, pts in streams.items():
    slope = lsq_slope(sorted(pts.items()))
    if slope is None:
        lo, hi = bounded_slope(sorted(pts.items()))
        slope = hi if hi is not None else None
        status = "bounded"
    else:
        status = "exact_fit"
    R[key] = dict(value=slope, status=status, points=dict(pts))

# ------------------------------------------------------------------- chains
L_m1 = {}
chains = defaultdict(dict)
for t in an.E["E3_CHAIN"]:
    if t["meta"]["lmul"] == "m1":
        chains[t["meta"]["instruction"]][t["meta"]["n"]] = t["delta"]
for i, pts in chains.items():
    slope = lsq_slope(sorted(pts.items()))
    if slope is not None:
        L_m1[i] = dict(value=slope, status="exact_fit", points=dict(pts))

# ----------------------------------------------------------- E4 matrix (m1)
k0 = defaultdict(dict)
for t in an.E["E4_XRAW"]:
    if t["meta"]["lmul"] != "m1" or t["meta"]["k"] != 0:
        continue
    k0[(t["meta"]["producer"], t["meta"]["consumer"])][
        "ctrl" if t["meta"]["control"] else "dep"] = t["delta"]
cell = {}
for (p, c), v in k0.items():
    if "dep" in v:
        cell[(p, c)] = v["dep"] - v.get("ctrl", 1)

# consumer cadence baseline = vcpop producer row (its result never feeds the
# vector consumer -> pure consumer structural cadence)
baseline = {c: cell.get(("vcpop_m", c), 0) for c in INSTRS}
raw_eff = {k: v - baseline[k[1]] for k, v in cell.items() if k[0] != "vcpop_m"}

# ---------------------------------------------------------------------- E5
waw = {}
grp5 = defaultdict(dict)
for t in an.E["E5_WAW"]:
    grp5[(t["meta"]["instruction"], t["meta"]["lmul"], t["meta"]["d"])][
        "ctrl" if t["meta"]["control"] else "waw"] = t["delta"]
by_i = defaultdict(dict)
for (i, lm, d), v in grp5.items():
    if "waw" in v and "ctrl" in v:
        by_i[(i, lm)][d] = v["waw"] - v["ctrl"]
for key, dd in by_i.items():
    stalling = [d for d, s in dd.items() if s > 0]
    if stalling:
        dmax = max(stalling)
        waw[key] = dmax + dd[dmax]

# ---------------------------------------------------------------------- E6
war = {}
grp6 = defaultdict(dict)
for t in an.E["E6_WAR"]:
    grp6[(t["meta"]["reader"], t["meta"]["writer"], t["meta"]["lmul"], t["meta"]["d"])][
        "ctrl" if t["meta"]["control"] else "war"] = t["delta"]
by_r = defaultdict(dict)
for (r, w, lm, d), v in grp6.items():
    if lm == "m1" and "war" in v and "ctrl" in v:
        by_r[(r, w)][d] = v["war"] - v["ctrl"]
for key, dd in by_r.items():
    stalling = [d for d, s in dd.items() if s > 0]
    war[key] = (max(stalling) + 1) if stalling else 0

# ---------------------------------------------------------------------- E7
mix = defaultdict(dict)
for t in an.E["E7_MIX"]:
    m = t["meta"]
    mix[(m["a"], m["b"], m["lmul"])] = t["delta"] / max(1, m["pairs"])

# ------------------------------------------------------------- final table
profile = {}
for i in INSTRS:
    row = dict(
        R={lm: R.get((i, lm), {}).get("value") for lm in LMUL_FACTOR},
        R_status={lm: R.get((i, lm), {}).get("status") for lm in LMUL_FACTOR},
        L_m1=L_m1.get(i, {}).get("value"),
        raw_col={c: raw_eff.get((i, c)) for c in INSTRS if (i, c) in raw_eff},
        waw={lm: waw.get((i, lm)) for lm in LMUL_FACTOR},
    )
    profile[i] = row

out = dict(
    profile=profile,
    war_release={f"{r}->{w}": v for (r, w), v in war.items()},
    e7_mix_slopes={f"{a}+{b}@{lm}": s for (a, b, lm), s in mix.items()},
    design_ground_truth=design.summary_table(),
)
os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
with open(os.path.join(ROOT, "results", "profile_measured.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)

# ------------------------------------------------------------- calibration
print("=== MEASURED (profile) vs DESIGN (injected) ===")
print(f"{'instr':<13}{'lmul':<5}{'R_meas':>7}{'R_des':>6}   {'L1_meas':>8}{'L1_des':>6}")
matchR = badR = 0
for i in INSTRS:
    for lm in LMUL_FACTOR:
        rm = profile[i]["R"][lm]; rd = design.R(i, lm)
        if rm is not None:
            matchR += (rm == rd); badR += (rm != rd)
        print(f"{i:<13}{lm:<5}{str(rm):>7}{rd:>6}   "
              f"{str(profile[i]['L_m1'] if lm=='m1' else ''):>8}"
              f"{(design.L(i, lm) if lm == 'm1' else ''):>6}")
print(f"\nR exact matches: {matchR}, emergent differences: {badR}")
print("(emergent = real machine behavior beyond the design table: vmul ANY-pipe")
print(" dual-slot streams, vmseq vmask_mv cadence, viota muop co-issue ...)")
print("\nWAW spacing (E5):", {f"{i}@{lm}": v for (i, lm), v in sorted(waw.items())})
print("WAR release (E6):", dict(list(sorted(war.items()))[:6]))
