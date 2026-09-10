#!/usr/bin/env python3
"""YuShuXin-V2 experiment assembly generator (E0-E11 differential suite).

Design principles (v2, replacing v1's T-series):
  - every template carries a CONTROL twin (same code, dependency severed) so
    inference is by DIFFERENCE, never by absolute interpretation;
  - filler instructions are scalar adds (cadence = 1 cycle, deterministic);
  - register allocation respects LMUL alignment and never creates accidental
    dependencies (v1's vcpop/m4 fetch-boundary trouble is avoided by keeping
    all timed regions straight-line with aligned 4-byte instructions only).

Outputs: experiments/<exp_id>/test.s + experiments/<exp_id>/experiment.json
"""
from __future__ import annotations
import argparse, json, os, itertools, re

LMULS = ("m1", "m2", "m4")
LMUL_FACTOR = {"m1": 1, "m2": 2, "m4": 4}
VL = {lm: 8 * LMUL_FACTOR[lm] for lm in LMULS}   # VLEN=256, SEW=32

# ---------------------------------------------------------------- machine map
INSTRUCTIONS = {
    "vadd_vv":     dict(asm="vadd.vv",     kind="vector", chainable=True,  args="vd, vs2, vs1"),
    "vmul_vv":     dict(asm="vmul.vv",     kind="vector", chainable=True,  args="vd, vs2, vs1"),
    "vdivu_vv":    dict(asm="vdivu.vv",    kind="vector", chainable=True,  args="vd, vs2, vs1"),
    "vmseq_vv":    dict(asm="vmseq.vv",    kind="mask",   chainable=False, args="vd, vs2, vs1"),
    "vredsum_vs":  dict(asm="vredsum.vs",  kind="vector", chainable=True,  args="vd, vs2, vs1"),
    "vslideup_vx": dict(asm="vslideup.vx", kind="vector", chainable=False, args="vd, vs2, rs1"),
    "vcpop_m":     dict(asm="vcpop.m",     kind="scalar", chainable=False, args="rd, vs2"),
    "viota_m":     dict(asm="viota.m",     kind="vector", chainable=False, args="vd, vs2"),
}

def groups(lmul: str, start: int = 0):
    """Aligned vector register group numbers for this LMUL."""
    step = LMUL_FACTOR[lmul]
    return list(range(start, 32, step))

def emit(instr: str, lmul: str, vd_group: int, src_a: int, src_b: int, xreg: int = 10):
    s = INSTRUCTIONS[instr]
    step = LMUL_FACTOR[lmul]
    a, b, d = f"v{src_a}", f"v{src_b}", f"v{vd_group}"
    if s["asm"] == "vslideup.vx":
        return f"vslideup.vx {d}, {a}, x6"
    if s["asm"] == "vcpop.m":
        return f"vcpop.m x{xreg}, {a}"
    if s["asm"] == "viota.m":
        return f"viota.m {d}, {a}"
    return f"{s['asm']} {d}, {a}, {b}"

# ------------------------------------------------------------------- program
def setup_block(lmul: str | None) -> list[str]:
    lines = ["    # ---- setup ----"]
    if lmul:
        lines += [f"    li x5, {VL[lmul]}",
                  f"    vsetvli x0, x5, e32, {lmul}, ta, ma"]
        for i, g in enumerate(groups(lmul)):
            lines.append(f"    vmv.v.i v{g}, {(i % 7) + 1}")
    for x in range(6, 32):
        lines.append(f"    li x{x}, {x}")
    return lines

def marker(exp: str, label: str) -> list[str]:
    sym = f"__yx_marker_{re.sub(r'[^A-Za-z0-9_]', '_', exp)}_{label}"
    return [f"    # TIMESTAMP_MARK {label}",
            f"    .globl {sym}",
            f"{sym}:"]

EXIT = ["    # ---- exit ----",
        "    li a7, 93", "    li a0, 0", "    ecall"]

def timed_prologue(exp: str) -> list[str]:
    """Align the timed region to a cache line and warm the icache for the
    epilogue with an unreachable shadow copy (fetch still populates I$)."""
    return ["    .balign 64",
            "    # ---- shadow warm-up of the epilogue (never executed) ----",
            "    j 1f"] + \
           ["    li a7, 93", "    li a0, 0", "    ecall", "1:"]

DRAIN = ["    # scalar drain (not timed)"] + \
        [f"    add x29, x30, x31" for _ in range(8)]

def filler_adds(k: int) -> list[str]:
    return [f"    add x2{1 + (i % 8)}, x6, x7   # filler {i}" for i in range(k)]

# --------------------------------------------------------------- generators
class Exp:
    def __init__(self, exp_id, template, body, meta):
        self.exp_id, self.template, self.body, self.meta = exp_id, template, body, meta
        self.meta.update(experiment_id=exp_id, template=template)

    def write(self, root):
        d = os.path.join(root, self.exp_id)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "test.s"), "w") as f:
            f.write(f"# {self.exp_id} [{self.template}]\n")
            f.write(".text\n.global _start\n_start:\n")
            f.write("\n".join(self.body) + "\n")
        with open(os.path.join(d, "experiment.json"), "w") as f:
            json.dump(self.meta, f, indent=1, sort_keys=True)

def e00():
    body = setup_block(None) + marker("e00-marker-baseline", "a") + marker("e00-marker-baseline", "b") + EXIT
    return Exp("e00-marker-baseline", "E0_BASELINE", body, {})

def e01(instr, lmul):
    g = groups(lmul)
    exp = f"e01-{instr}-{lmul}"
    body = (setup_block(lmul) + timed_prologue(exp) + marker(exp, "start") +
            [f"    {emit(instr, lmul, g[2], g[0], g[1])}"] +
            marker(exp, "end") + EXIT)
    return Exp(exp, "E1_KILLCHECK", body, dict(instruction=instr, lmul=lmul))

def e02(instr, lmul, n):
    g = groups(lmul)
    outs = [x for x in g if x not in (g[0], g[1])]
    if len(outs) < n:
        raise ValueError(f"{instr}@{lmul}: only {len(outs)} dest groups for N={n}")
    exp = f"e02-{instr}-{lmul}-n{n}"
    body = (setup_block(lmul) + timed_prologue(exp) + marker(exp, "start") +
            [f"    {emit(instr, lmul, outs[i % len(outs)], g[0], g[1])}   # stream {i}"
             for i in range(n)] +
            marker(exp, "end") + EXIT)
    return Exp(exp, "E2_STREAM", body, dict(instruction=instr, lmul=lmul, n=n))

def e03(instr, lmul, n):
    g = groups(lmul)
    dest = g[2]
    exp = f"e03-{instr}-{lmul}-n{n}"
    body = (setup_block(lmul) + timed_prologue(exp) + marker(exp, "start") +
            [f"    {emit(instr, lmul, dest, g[0], g[1])}   # seed"] +
            [f"    {emit(instr, lmul, dest, dest, g[1])}   # chain {i}" for i in range(n - 1)] +
            marker(exp, "end") + EXIT)
    return Exp(exp, "E3_CHAIN", body, dict(instruction=instr, lmul=lmul, n=n))

def _consumer(instr_p, lmul, prod_group, ctrl_group, consumer, control=False):
    """Emit a consumer reading the producer's result (or a control register)."""
    src = ctrl_group if control else prod_group
    if consumer == "scalar_add":
        return [f"    add x11, x10, x0   # scalar consumer"]
    if consumer == "vcpop_m":
        return [f"    vcpop.m x11, {src}   # mask consumer"]
    g = groups(lmul)
    return [f"    {emit(consumer, lmul, g[3], src, g[1])}   # consumer {consumer}"]

def _producer_dest(instr, lmul):
    g = groups(lmul)
    return g[2]           # v-d group; for vcpop it is x10 via xreg=10

def e04(instr_p, consumer, lmul, k, control=False):
    g = groups(lmul)
    prod_group = _producer_dest(instr_p, lmul)
    ctrl_group = g[6] if len(g) > 6 else g[1]
    tag = "ctrl" if control else "dep"
    exp = f"e04-{instr_p}-x-{consumer}-{lmul}-k{k}-{tag}"
    body = (setup_block(lmul) + timed_prologue(exp) + marker(exp, "start") +
            [f"    {emit(instr_p, lmul, prod_group, g[0], g[1])}   # producer"] +
            [f"    add x2{1 + (i % 8)}, x6, x7   # filler {i}" for i in range(k)] +
            _consumer(instr_p, lmul, prod_group, ctrl_group, consumer, control=control) +
            marker(exp, "end") + EXIT)
    return Exp(exp, "E4_XRAW", body,
               dict(producer=instr_p, consumer=consumer, lmul=lmul, k=k, control=control))

def e05(instr, lmul, d, control=False):
    g = groups(lmul)
    same = _producer_dest(instr, lmul)
    other = g[3] if len(g) > 3 else g[2]
    second = same if not control else other
    tag = "ctrl" if control else "waw"
    exp = f"e05-{instr}-{lmul}-d{d}-{tag}"
    body = (setup_block(lmul) + timed_prologue(exp) + marker(exp, "start") +
            [f"    {emit(instr, lmul, same, g[0], g[1])}   # write1 -> v{same}"] +
            filler_adds(d) +
            [f"    {emit(instr, lmul, second, g[4] if len(g) > 4 else g[1], g[5] if len(g) > 5 else g[1])}   # write2 -> v{second}"] +
            marker(exp, "end") + EXIT)
    return Exp(exp, "E5_WAW", body, dict(instruction=instr, lmul=lmul, d=d, control=control))

def e06(reader, writer, lmul, d, control=False):
    g = groups(lmul)
    src = g[0]           # reader reads v0-group
    wdest = src if not control else g[5]
    tag = "ctrl" if control else "war"
    exp = f"e06-{reader}-{writer}-{lmul}-d{d}-{tag}"
    body = (setup_block(lmul) + timed_prologue(exp) + marker(exp, "start") +
            [f"    {emit(reader, lmul, g[2], src, g[1])}   # reader of v{src}"] +
            filler_adds(d) +
            [f"    {emit(writer, lmul, wdest, g[4] if len(g) > 4 else g[1], g[5] if len(g) > 5 else g[1])}   # writer -> v{wdest}"] +
            marker(exp, "end") + EXIT)
    return Exp(exp, "E6_WAR", body, dict(reader=reader, writer=writer, lmul=lmul, d=d, control=control))

def e07(a, b, lmul, pairs=4):
    g = groups(lmul)
    da, db = g[2], g[3] if len(g) > 3 else g[2]
    exp = f"e07-{a}-{b}-{lmul}-p{pairs}"
    seq = []
    for i in range(pairs):
        seq.append(f"    {emit(a, lmul, da, g[0], g[1])}   # A{i}")
        seq.append(f"    {emit(b, lmul, db, g[0], g[1])}   # B{i}")
    body = setup_block(lmul) + timed_prologue(exp) + marker(exp, "start") + seq + marker(exp, "end") + EXIT
    return Exp(exp, "E7_MIX", body, dict(a=a, b=b, lmul=lmul, pairs=pairs))

def e08(instr, lmul, mode="sv", pairs=4):
    """mode: sv = scalar+vector, vs/pair handled by e07; triple = scalar+vec+vec."""
    g = groups(lmul)
    exp = f"e08-{instr}-{lmul}-{mode}-p{pairs}"
    body = setup_block(lmul) + timed_prologue(exp) + marker(exp, "start")
    for i in range(pairs):
        if mode == "sv":
            body += [f"    add x2{1 + (i % 8)}, x6, x7",
                     f"    {emit(instr, lmul, g[2 + (i % 2)], g[0], g[1])}"]
        elif mode == "triple":
            body += [f"    add x2{1 + (i % 8)}, x6, x7",
                     f"    {emit(instr, lmul, g[2], g[0], g[1])}",
                     f"    add x2{2 + (i % 7)}, x6, x7"]
    body += marker(exp, "end") + EXIT
    return Exp(exp, "E8_ISSUE", body, dict(instruction=instr, lmul=lmul, mode=mode, pairs=pairs))

def e10(lmul, k=0):
    g = groups(lmul)
    exp = f"e10-loadhit-{lmul}-k{k}"
    body = (["    # ---- setup ----",
             "    la x8, __yx_load_data",
             f"    li x5, {VL[lmul]}",
             f"    vsetvli x0, x5, e32, {lmul}, ta, ma"] +
            ["    vmv.v.i v0, 1", "    li x6, 6", "    li x7, 7"] +
            [f"    vle32.v v{g[0]}, (x8)   # warm",
             f"    vle32.v v{g[1]}, (x8)   # warm"] +
            timed_prologue(exp) + marker(exp, "start") +
            [f"    vle32.v v{g[2]}, (x8)   # measured load"] +
            filler_adds(k) +
            [f"    vadd.vv v{g[3]}, v{g[2]}, v{g[0]}   # consumer"] +
            marker(exp, "end") + EXIT +
            ["    .section .data", "    .balign 64", "__yx_load_data:"] +
            [f"    .word {i + 1}" for i in range(64)])
    return Exp(exp, "E10_LOAD", body, dict(lmul=lmul, k=k))

# ------------------------------------------------------------------- suite
def build_suite():
    exps = [e00()]
    L = lambda i, lm: None  # filled by analyzer; here we just bound sweeps generically
    for instr, lmul in itertools.product(INSTRUCTIONS, LMULS):
        exps.append(e01(instr, lmul))
        maxn = len([x for x in groups(lmul) if x not in groups(lmul)[:2]])
        for n in (2, 3, 4, 6, 8, 12):
            if n <= maxn:
                exps.append(e02(instr, lmul, n))
        if INSTRUCTIONS[instr]["chainable"]:
            for n in (2, 3, 4, 6, 12):
                exps.append(e03(instr, lmul, n))
        # E4: default-consumer k sweep + control + all-consumer k0 matrix
        default_c = {"vector": "vadd_vv", "mask": "vcpop_m", "scalar": "scalar_add"}[INSTRUCTIONS[instr]["kind"]]
        for k in range(0, 31):
            exps.append(e04(instr, default_c, lmul, k))
            if k % 3 == 0:
                exps.append(e04(instr, default_c, lmul, k, control=True))
        for c in INSTRUCTIONS:
            exps.append(e04(instr, c, lmul, 0))
        # E5 WAW sweep + control twin at every d (differential requirement)
        for d in range(0, 29):
            exps.append(e05(instr, lmul, d))
            exps.append(e05(instr, lmul, d, control=True))
    # E6 WAR: reader=vadd (VP0) and vdivu (VP1, read_lat=2), writers across classes
    for reader in ("vadd_vv", "vdivu_vv"):
        for writer in INSTRUCTIONS:
            for lmul in LMULS:
                for d in range(0, 7):
                    exps.append(e06(reader, writer, lmul, d))
                exps.append(e06(reader, writer, "m1", 0, control=True))
                exps.append(e06(reader, writer, "m1", 3, control=True))
    # E7 all unordered pairs (incl. self pairs) at m1 + m4
    for a, b in itertools.combinations_with_replacement(INSTRUCTIONS, 2):
        for lmul in ("m1", "m4"):
            exps.append(e07(a, b, lmul))
    # E8
    for instr, lmul in itertools.product(INSTRUCTIONS, LMULS):
        exps.append(e08(instr, lmul, "sv"))
    exps.append(e08("vadd_vv", "m1", "triple"))
    exps.append(e08("vdivu_vv", "m1", "triple"))
    # E10 loads
    for lmul in LMULS:
        for k in (0, 2, 4, 6):
            exps.append(e10(lmul, k))
    return exps

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="experiments")
    ap.add_argument("--suite", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    exps = build_suite()
    if args.list:
        for e in exps:
            print(e.exp_id)
        print(f"# total {len(exps)}")
        return
    for e in exps:
        e.write(args.out)
    print(f"wrote {len(exps)} experiments under {args.out}/")

if __name__ == "__main__":
    main()
