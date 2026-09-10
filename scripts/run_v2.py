#!/usr/bin/env python3
"""YuShuXin-V2 experiment runner.

Backends:
  --backend analytic   marker cycles computed by scripts/yxmodel.py (the ONE
                       formula source; used to sanity-check the analyzer)
  --backend gem5       assemble with llvm-mc, link with ld.lld, resolve marker
                       symbols with llvm-nm, run gem5.opt (RiscvMinorCPU +
                       our FU pool config), parse the Exec debug log, convert
                       tick -> cycle @1GHz.

Every experiment directory produced by gen_asm_v2.py contains test.s and
experiment.json; this runner writes trace.json next to them.
"""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yxmodel import TimingModel, LMUL_FACTOR  # noqa: E402

LLVM_BIN = "/home/zhaosiying/codebase/llvm-project/build/bin"
GEM5 = "/home/zhaosiying/codebase/gem5/build/RISCV/gem5.opt"
GEM5_CFG = "/home/zhaosiying/codebase/gem5/configs/yushuxin/se_yushuxin.py"
TICKS_PER_CYCLE = 1000  # 1 GHz

# ------------------------------------------------------------------ toolchain
def run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)
    if p.returncode != 0:
        raise RuntimeError(f"cmd failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr[-2000:]}")
    return p.stdout

def build_elf(test_s: str, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    obj = os.path.join(outdir, "test.o")
    elf = os.path.join(outdir, "test.elf")
    asm = os.path.join(outdir, "test.lowered.s")
    # marker lowering: TIMESTAMP_MARK is already lowered by gen_asm_v2 (labels);
    # file is used verbatim.
    shutil.copyfile(test_s, asm)
    run([f"{LLVM_BIN}/llvm-mc", "-triple=riscv64", "-mattr=+v,+zvl256b",
         "-filetype=obj", "-o", obj, asm])
    run([f"{LLVM_BIN}/ld.lld", "-m", "elf64lriscv", "--no-relax",
         "-Ttext=0x80000000", "-o", elf, obj])
    return elf

def resolve_markers(elf: str) -> dict[str, int]:
    out = run([f"{LLVM_BIN}/llvm-nm", "-n", elf])
    marks = {}
    for line in out.splitlines():
        m = re.match(r"^([0-9a-fA-F]+)\s+\S\s+(__yx_marker_\S+)$", line.strip())
        if m:
            marks[m.group(2)] = int(m.group(1), 16)
    return marks

def run_gem5(elf: str, outdir: str, max_seconds=180):
    cmd = [GEM5, "--outdir", os.path.join(outdir, "gem5"),
           "--debug-flags=Exec", "--debug-file=exec.log",
           GEM5_CFG, "--cmd", elf]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=max_seconds)
    log = os.path.join(outdir, "gem5", "exec.log")
    if not os.path.exists(log):
        raise RuntimeError(f"gem5 produced no exec.log rc={p.returncode}\n{p.stderr[-2000:]}")
    return log, p.returncode

EXEC_RE = re.compile(r"^(\d+)\s+.*0x([0-9a-fA-F]+) <?.*")

def parse_exec_cycles(log: str, marker_pcs: dict[int, object]) -> dict[int, int]:
    """First tick at which each marker PC appears in the Exec log."""
    want = set(marker_pcs)
    found: dict[int, int] = {}
    with open(log, errors="replace") as f:
        for line in f:
            if not want:
                break
            m = re.match(r"^\s*(\d+):", line)
            if not m:
                continue
            for pc_field in re.findall(r"0x([0-9a-fA-F]{8,16})", line[:120]):
                pc = int(pc_field, 16)
                if pc in want and pc not in found:
                    found[pc] = int(m.group(1))
    return {pc: tick // TICKS_PER_CYCLE for pc, tick in found.items()}

# ------------------------------------------------------------------- backends
def backend_gem5(exp_dir: str, m: TimingModel):
    test_s = os.path.join(exp_dir, "test.s")
    meta = json.load(open(os.path.join(exp_dir, "experiment.json")))
    outdir = os.path.join(exp_dir, "build")
    elf = build_elf(test_s, outdir)
    marks = resolve_markers(elf)
    exp = meta["experiment_id"]
    import re as _re
    safe = _re.sub(r"[^A-Za-z0-9_]", "_", exp)
    names = {k: v for k, v in marks.items() if k.startswith(f"__yx_marker_{safe}_")}
    log, rc = run_gem5(elf, outdir)
    pc_to_cycle = parse_exec_cycles(log, {pc: None for pc in names.values()})
    entries = []
    for name, pc in sorted(names.items(), key=lambda kv: (kv[1], kv[0])):
        label = name.rsplit("_", 1)[-1]
        entries.append(dict(marker=label, cycle=pc_to_cycle.get(pc), pc=hex(pc)))
    trace = dict(schema_version=2, experiment_id=exp, backend="gem5_minor",
                 mode="real_platform_profile", template=meta["template"],
                 meta=meta, entries=entries, gem5_rc=rc,
                 marker_baseline_cycles=0)
    json.dump(trace, open(os.path.join(exp_dir, "trace.json"), "w"), indent=1)
    return trace

def backend_analytic(exp_dir: str, m: TimingModel):
    meta = json.load(open(os.path.join(exp_dir, "experiment.json")))
    t = meta["template"]
    exp = meta["experiment_id"]
    lm = meta.get("lmul", "m1")

    def delta():
        if t == "E0_BASELINE":
            return 0
        if t == "E1_KILLCHECK":
            return m.L(meta["instruction"], lm)
        if t == "E2_STREAM":
            return m.stream_delta(meta["instruction"], lm, meta["n"])
        if t == "E3_CHAIN":
            return m.chain_delta(meta["instruction"], lm, meta["n"])
        if t == "E4_XRAW":
            if meta["control"]:
                return meta["k"] + 1          # fillers + consumer, no stall
            return m.xraw_delta(meta["producer"], meta["consumer"], lm, meta["k"])
        if t == "E5_WAW":
            base = meta["d"]
            need = m.waw_min_spacing(meta["instruction"], lm)
            stall = max(0, need - base) if not meta["control"] else 0
            return base + stall + 1
        if t == "E6_WAR":
            base = meta["d"]
            need = m.war_min_spacing(meta["reader"]) if not meta["control"] else 0
            return base + max(0, need - base) + 1
        if t == "E7_MIX":
            slope, verdict = m.mix_pair_slope(meta["a"], meta["b"], lm)
            return meta["pairs"] * slope
        if t == "E8_ISSUE":
            R = m.R(meta["instruction"], lm)
            return meta["pairs"] * max(R, 1)  # sv pairs: dual-issue every cycle
        if t == "E10_LOAD":
            need = m.load_lat + 1
            stall = max(0, need - meta["k"]) if meta["k"] else need
            return meta["k"] + stall + 1
        raise ValueError(t)

    d = delta()
    trace = dict(schema_version=2, experiment_id=exp, backend="analytic_yxmodel",
                 mode="synthetic_calibration", template=t, meta=meta,
                 entries=[dict(marker="start", cycle=1000, pc="0x80000000"),
                          dict(marker="end", cycle=1000 + d, pc="0x80000004")],
                 marker_baseline_cycles=0)
    json.dump(trace, open(os.path.join(exp_dir, "trace.json"), "w"), indent=1)
    return trace

# ----------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp_dir")
    ap.add_argument("--backend", choices=("gem5", "analytic"), default="gem5")
    args = ap.parse_args()
    m = TimingModel(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "config", "yushuxin_timing_v2.yaml"))
    t = backend_gem5(args.exp_dir, m) if args.backend == "gem5" else backend_analytic(args.exp_dir, m)
    s = {e["marker"]: e["cycle"] for e in t["entries"]}
    keys = sorted(s)
    if len(keys) >= 2:
        print(f"{t['experiment_id']}: delta = {s[keys[-1]] - s[keys[0]]}")

if __name__ == "__main__":
    main()
