#!/usr/bin/env python3
"""YuShuXin-V2.1 unified analytic machine model (single formula source).

Consumed by:
  1. scripts/run_v2.py               -- analytic backend
  2. scripts/verify_timing_exactness.py -- design-invariant gate vs gem5
  3. scripts/analyze_v2.py           -- closed-form inversion cross-check

Config: config/yushuxin_timing_v2.yaml (micro-op level parameters).
Macro semantics (FROZEN against the injected gem5 machine):
  - a macro splits into lambda micro-ops issued issueLat(mu) apart inside the
    macro (viota at mu=1 co-issues both muops in one cycle; vredsum/vslideup
    at mu=2 spread them; vcpop.m does not split at all);
  - vmseq.vv splits into a SimdCmp muop + a vmask_mv (SimdAdd) companion that
    carries the mask write -- its cadence follows the SimdAdd path;
  - stream macro-to-macro spacing and chain intervals are EMERGENT: streams
    are what E2 measures (the analyzer recovers R from them); the design
    invariants that ARE promised and gated:
        I0  marker delta == 0
        I1  m1 chain interval == max(opLat - srcLat, mu)  (direct chains)
            vmseq chains ride the vmask_mv path: interval == 4
        I2  non-pipelined divider: R == L == lambda*opLat
        I3  micro-ops inside a macro are mu apart (mu > 1)
"""
from __future__ import annotations
import os
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CFG = os.path.join(HERE, "..", "config", "yushuxin_timing_v2.yaml")
LMUL_FACTOR = {"m1": 1, "m2": 2, "m4": 4}

# gem5 v24.1.0.3 decoder OpClass per instruction (verified in decoder.isa):
OPCLASS = {
    "vadd_vv": "SimdAdd", "vmul_vv": "SimdMult", "vdivu_vv": "SimdDiv",
    "vmseq_vv": "SimdCmp", "vredsum_vs": "SimdReduceAdd",
    "vslideup_vx": "SimdAlu", "vcpop_m": "SimdAlu", "viota_m": "SimdAlu",
}


class TimingModel:
    def __init__(self, path: str = DEFAULT_CFG):
        self.cfg = yaml.safe_load(open(path))
        g = self.cfg["globals"]
        self.issue_width = g["issue_width"]
        self.load_lat = g["load_hit_latency"]
        self.vlsu_beats = g["vlsu_beats"]
        self.instrs = self.cfg["instructions"]
        self.fus = {f["name"]: f for f in self.cfg["fu_pools"]}

    # ------------------------------------------------------------- helpers
    def _fu(self, instr):
        fu = self.instrs[instr]["fu"]
        return fu[0] if isinstance(fu, list) else fu

    def mu(self, instr):
        return self.fus[self._fu(instr)]["mu"]

    def opLat(self, instr):
        return self.fus[self._fu(instr)]["opLat"]

    def src_lat(self, instr):
        return self.instrs[instr]["src_lat"]

    def pipe(self, instr):
        fus = self.instrs[instr]["fu"]
        fus = fus if isinstance(fus, list) else [fus]
        pipes = {self.fus[f]["pipe"] for f in fus}
        return "ANY" if len(pipes) > 1 else pipes.pop()

    def is_nonpipelined(self, instr):
        return self.fus[self._fu(instr)].get("nonpipelined", False)

    def nosplit(self, instr):
        return self.instrs[instr].get("nosplit", False)

    # --------------------------------------------------- macro observables
    def L(self, instr, lmul):
        lam = LMUL_FACTOR[lmul]
        if self.nosplit(instr):
            return self.instrs[instr]["l_micro"]
        if self.is_nonpipelined(instr):
            return lam * self.opLat(instr)
        return self.instrs[instr]["l_micro"] + (lam - 1) * self.mu(instr)

    def R(self, instr, lmul):
        lam = LMUL_FACTOR[lmul]
        if self.nosplit(instr):
            return 1
        if self.is_nonpipelined(instr):
            return self.L(instr, lmul)
        return lam * self.mu(instr)

    def l_eff(self, instr):
        """m1 RAW chain interval (bypassed)."""
        return max(self.opLat(instr) - self.src_lat(instr), self.mu(instr))

    def waw(self, instr, lmul):
        lam = LMUL_FACTOR[lmul]
        return (0 if self.nosplit(instr) else (lam - 1) * self.mu(instr)) \
            + self.opLat(instr) + self.instrs[instr].get("extra_commit_lat", 0)

    def read_lat(self, instr):
        return self.src_lat(instr)

    def raw_penalty(self, producer, consumer):
        if consumer == "scalar_add":
            return self.src_lat(producer)
        pp, cp = self.pipe(producer), self.pipe(consumer)
        if pp != "ANY" and cp != "ANY" and pp != cp:
            return self.src_lat(producer)
        return 0

    # --------------------------------------------------- delta formulas
    def stream_delta(self, instr, lmul, n):
        return n * self.R(instr, lmul) - self.mu(instr)

    def chain_interval(self, instr, lmul):
        lam = LMUL_FACTOR[lmul]
        if self.nosplit(instr):
            return max(self.opLat(instr) - self.src_lat(instr), 1)
        if self.is_nonpipelined(instr):
            return self.R(instr, lmul)
        return (lam - 1) * self.mu(instr) + self.opLat(instr) - self.src_lat(instr)

    def chain_delta(self, instr, lmul, n):
        lam = LMUL_FACTOR[lmul]
        tail = 0 if self.nosplit(instr) else (lam - 1) * self.mu(instr)
        return (n - 1) * self.chain_interval(instr, lmul) + tail

    def mix_pair_slope(self, a, b, lmul):
        Ra, Rb = self.R(a, lmul), self.R(b, lmul)
        pa, pb = self.pipe(a), self.pipe(b)
        if pa != "ANY" and pb != "ANY" and pa == pb:
            return Ra + Rb, "serial"
        return max(Ra, Rb), "parallel"

    # ------------------------------------------------------------- helpers
    def all_classes(self):
        return list(self.instrs.keys())

    def summary_table(self):
        import itertools
        rows = []
        for i, lm in itertools.product(self.all_classes(), LMUL_FACTOR):
            rows.append({
                "instr": i, "lmul": lm, "L": self.L(i, lm), "R": self.R(i, lm),
                "pipe": self.pipe(i), "pipelined": not self.is_nonpipelined(i),
                "waw": self.waw(i, lm), "read_lat": self.read_lat(i),
            })
        return rows


if __name__ == "__main__":
    m = TimingModel()
    print(f"{'instr':<13}{'lmul':<5}{'L':>4}{'R':>4}  {'pipe':<5}{'waw':>4}{'rdlat':>6}")
    for r in m.summary_table():
        print(f"{r['instr']:<13}{r['lmul']:<5}{r['L']:>4}{r['R']:>4}  "
              f"{r['pipe']:<5}{r['waw']:>4}{r['read_lat']:>6}")
    print("\nsanity: vdivu non-pipelined R==L:",
          all(m.R('vdivu_vv', lm) == m.L('vdivu_vv', lm) for lm in LMUL_FACTOR))
