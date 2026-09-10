#!/usr/bin/env python3
"""E11: composite additivity — one program, marked segments of every primitive
shape separated by scalar drains. Asserts: measured per-segment deltas equal
the yxmodel closed forms (machine behavior is additive across segments; the
marker method composes). Writes results/composite_e11.json and prints a table.
"""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yxmodel import TimingModel
from run_v2 import build_elf, resolve_markers, run_gem5, parse_exec_cycles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = TimingModel(os.path.join(ROOT, "config", "yushuxin_timing_v2.yaml"))
EXP = "e11_composite"

def marker(label):
    sym = f"__yx_marker_{EXP}_{label}"
    return [f"    .globl {sym}", f"{sym}:"]

DRAIN = [f"    add x2{1+(i%8)}, x6, x7   # drain" for i in range(6)]

SEGMENTS = [
    ("stream_vadd_m1", m.stream_delta("vadd_vv", "m1", 6),
     [f"    vadd.vv v{2+i}, v0, v1" for i in range(6)]),
    ("chain_vdivu_m1", m.chain_delta("vdivu_vv", "m1", 3),
     ["    vdivu.vv v2, v0, v1", "    vdivu.vv v2, v2, v1", "    vdivu.vv v2, v2, v1"]),
    ("stream_vredsum_m2", m.stream_delta("vredsum_vs", "m2", 3),
     ["    vredsum.vs v4, v0, v2", "    vredsum.vs v6, v0, v2", "    vredsum.vs v8, v0, v2"]),
    ("xraw_vslideup_to_vadd_m1", m.l_eff("vslideup_vx") + 2,
     ["    vslideup.vx v2, v4, x6", "    vadd.vv v6, v2, v0"]),
    ("mix_vadd_vredsum_m1", 2 * 2 + 1,
     ["    vadd.vv v10, v0, v1", "    vredsum.vs v12, v0, v2",
      "    vadd.vv v14, v0, v1", "    vredsum.vs v16, v0, v2"]),
]

body = ["    # ---- setup ----", "    li x5, 8", "    vsetvli x0, x5, e32, m1, ta, ma",
        "    li x6, 6", "    li x7, 7", "    li t2, 2",
        "    vmv.v.i v0, 1", "    vmv.v.i v1, 2", "    vmv.v.i v2, 3", "    vmv.v.i v4, 4"]
# m2 segment needs its own vsetvli + restore
segs_asm = []
labels = []
for name, expect, code in SEGMENTS:
    if name.startswith("stream_vredsum_m2"):
        segs_asm += DRAIN + ["    li x5, 16", "    vsetvli x0, x5, e32, m2, ta, ma"] + marker(name + "_start")
        segs_asm += ["    " + c.strip() for c in code]
        segs_asm += marker(name + "_end") + ["    li x5, 8", "    vsetvli x0, x5, e32, m1, ta, ma"]
    else:
        segs_asm += DRAIN + marker(name + "_start")
        segs_asm += ["    " + c.strip() for c in code]
        segs_asm += marker(name + "_end")
    labels.append(name)

body += segs_asm + ["    li a7, 93", "    li a0, 0", "    ecall"]

d = os.path.join(ROOT, "experiments", EXP)
os.makedirs(d, exist_ok=True)
open(os.path.join(d, "test.s"), "w").write(
    f"# {EXP}\n.text\n.global _start\n_start:\n" + "\n".join(body) + "\n")
json.dump({"experiment_id": EXP, "template": "E11_COMPOSITE"},
          open(os.path.join(d, "experiment.json"), "w"))

elf = build_elf(os.path.join(d, "test.s"), os.path.join(d, "build"))
marks = resolve_markers(elf)
log, rc = run_gem5(elf, os.path.join(d, "build"))
cyc = parse_exec_cycles(log, {pc: None for pc in marks.values()})

rows = []
ok = bad = 0
for name, expect, _ in SEGMENTS:
    s = cyc.get(marks[f"__yx_marker_{EXP}_{name}_start"])
    e = cyc.get(marks[f"__yx_marker_{EXP}_{name}_end"])
    if s is None or e is None:
        rows.append((name, None, expect, "MISSING")); bad += 1; continue
    got = e - s
    match = (got == expect)
    ok += match; bad += (not match)
    rows.append((name, got, expect, "OK" if match else "MISMATCH"))

print(f"{'segment':<28}{'measured':>9}{'expected':>9}   verdict")
for r in rows:
    print(f"{r[0]:<28}{str(r[1]):>9}{r[2]:>9}   {r[3]}")
print(f"E11 COMPOSITE: ok={ok} bad={bad}")
json.dump({"rows": rows, "ok": ok, "bad": bad},
          open(os.path.join(ROOT, "results", "composite_e11.json"), "w"), indent=1)
sys.exit(1 if bad else 0)
