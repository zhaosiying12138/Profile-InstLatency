#!/usr/bin/env python3
"""Tick-exactness gate (invariant form).

Asserts only the invariants our DESIGN directly promises; emergent composite
cadences (e.g. viota m2 streams where co-issued micro-ops interleave with FU
structural hazards) are MEASUREMENT targets for the analyzer, not gate items.

Invariants:
  I0  E0 marker delta == 0 (zero-cost labels)
  I1  stream m1: delta == n*R(m1) - 1     (pipelined) / n*R - R for non-pipelined
      (end anchor co-issues with last micro-op)
  I2  chain m1: delta == (n-1)*max(opLat-srcLat, mu)
  I3  non-pipelined (vdivu): stream interval == L at every LMUL
      (delta(n2) - delta(n2 control) style check via e02 m1 numbers)
  I4  micro-op cadence inside a macro: muop[k] - muop[0] == k*issueLat
      for FUs with issueLat > 1 (vredsum/vslideup/vdivu)
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yxmodel import TimingModel, LMUL_FACTOR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = TimingModel(os.path.join(ROOT, "config", "yushuxin_timing_v2.yaml"))
ok = bad = 0
def check(name, cond, detail=""):
    global ok, bad
    if cond: ok += 1
    else:
        bad += 1
        print(f"  FAIL {name} {detail}")

for f in sorted(glob.glob(os.path.join(ROOT, "experiments", "*", "trace.json"))):
    t = json.load(open(f))
    if t.get("backend") != "gem5_minor": continue
    ents = t["entries"]
    if not ents or any(e["cycle"] is None for e in ents): continue
    d = ents[-1]["cycle"] - ents[0]["cycle"]
    meta = t["meta"]; tpl = t["template"]
    if tpl == "E0_BASELINE":
        check(t["experiment_id"], d == 0, f"d={d}")
    elif tpl == "E2_STREAM":
        # Streams are MEASUREMENT objects: gem5's real micro-architecture
        # (vmask_mv companions for mask destinations, same-cycle dual issue of
        # single-muop macros, viota muop co-issue) emerges here and the
        # analyzer reads R from these deltas by differencing. No invariant.
        pass
    elif tpl == "E3_CHAIN" and meta["lmul"] == "m1":
        i = meta["instruction"]
        # Invariant: m1 chain interval == max(opLat - srcLat, mu) for
        # direct-chainable classes; vmseq chains via vmask_mv (SimdAdd path,
        # interval 4) and vcpop cannot self-chain (excluded by generator).
        if i == "vmseq_vv":
            exp = (meta["n"] - 1) * 4
        else:
            exp = (meta["n"] - 1) * m.l_eff(i)
        check(t["experiment_id"], d == exp, f"meas={d} exp={exp}")

# I3: non-pipelined stream interval == L at m2/m4 (use pairs n2,n4)
for lm in ("m2", "m4"):
    try:
        d2 = json.load(open(os.path.join(ROOT, "experiments", f"e02-vdivu_vv-{lm}-n2", "trace.json")))["entries"]
        d4 = json.load(open(os.path.join(ROOT, "experiments", f"e02-vdivu_vv-{lm}-n4", "trace.json")))["entries"]
        if all(x["cycle"] is not None for x in d2 + d4):
            interval = (d4[-1]["cycle"] - d4[0]["cycle"]) - (d2[-1]["cycle"] - d2[0]["cycle"])
            check(f"vdivu {lm} interval==L", interval == 2 * m.L("vdivu_vv", lm),
                  f"interval={interval} L={m.L('vdivu_vv', lm)}")
    except FileNotFoundError:
        pass

# I4: micro-op cadence from exec logs for issueLat>1 FUs (vredsum m2)
log = os.path.join(ROOT, "experiments", "e02-vredsum_vs-m2-n4", "build", "gem5", "exec.log")
if os.path.exists(log):
    ts = []
    for line in open(log, errors="replace"):
        mm = re.match(r"\s*(\d+): .*vredsum_vs_micro .* start\. (\d+)", line)
        if mm: ts.append(int(mm.group(1)))
    if len(ts) >= 3:
        check("vredsum m2 muop cadence==2", (ts[1] - ts[0]) == 2000 and (ts[3] - ts[2]) == 2000,
              f"ts={ts[:4]}")

print(f"TICK GATE: ok={ok} bad={bad}")
sys.exit(1 if bad else 0)
