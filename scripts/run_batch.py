#!/usr/bin/env python3
"""Batch-run experiments (sequential; each takes ~3-6s of gem5)."""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPS = os.path.join(ROOT, "experiments")

def core_set():
    ids = []
    INSTRS = ["vadd_vv","vmul_vv","vdivu_vv","vmseq_vv","vredsum_vs","vslideup_vx","vcpop_m","viota_m"]
    LMULS = ["m1","m2","m4"]
    for i in INSTRS:
        for lm in LMULS:
            ids.append(f"e01-{i}-{lm}")
            for n in (2,3,4,6,8,12):
                d = os.path.join(EXPS, f"e02-{i}-{lm}-n{n}")
                if os.path.isdir(d):
                    ids.append(f"e02-{i}-{lm}-n{n}")
            for n in (2,4,12):
                d = os.path.join(EXPS, f"e03-{i}-{lm}-n{n}")
                if os.path.isdir(d):
                    ids.append(f"e03-{i}-{lm}-n{n}")
            # E4 default consumer k-sweep (cap k at 30 in generator) + every 3rd control
            for e in sorted(os.listdir(EXPS)):
                if e.startswith(f"e04-{i}-x-") and e.endswith(f"-{lm}-k0-dep"):
                    ids.append(e)
    return ids

def main():
    exps = sys.argv[1:] if len(sys.argv) > 1 else core_set()
    t0 = time.time(); ok = bad = 0
    for k, eid in enumerate(exps):
        d = os.path.join(EXPS, eid)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "run_v2.py"),
                            d, "--backend", "gem5"], capture_output=True, text=True)
        good = os.path.exists(os.path.join(d, "trace.json")) and r.returncode == 0
        ok += good; bad += (not good)
        if (k+1) % 25 == 0:
            print(f"[{k+1}/{len(exps)}] ok={ok} bad={bad} elapsed={time.time()-t0:.0f}s", flush=True)
    print(f"DONE ok={ok} bad={bad} total={len(exps)} secs={time.time()-t0:.0f}")

if __name__ == "__main__":
    main()
