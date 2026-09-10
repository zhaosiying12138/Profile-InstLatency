#!/usr/bin/env python3
"""YuShuXin-V2 analyzer: invert machine parameters from trace deltas.

Every inference is DIFFERENTIAL (dependent run minus its control twin) and
closed-form. Output: results/profile_v2.yaml + results/evidence_matrix.json.

Inversions (all per instruction i, lmul lm):
  R(i,lm)   E2 slope: R = (d(n2)-d(n1))/(n2-n1)  (n-scan least squares)
            non-pipelined test: E2 slope == E3 slope => R == L
  L(i,lm)   E3 slope (chainable) else E4: L = (d_dep(k*) - d_ctrl(k*)) - 1
            at the k* where the stall just vanishes; cross-check vs E10-style
            load runs is structural only.
  pen(p->c) E4 matrix at k=0: d_dep - d_ctrl - 1 - L(p)
            => cluster into same-pipe(0)/cross-pipe(G3)/vec->gpr(G4)
  waw(i,lm) E5: minimal d with d_dep == d_ctrl  => spacing = L + waw_extra
  read_lat  E6: minimal d with d_war == d_ctrl
  pipes     E7: parallel vs serial vs partial(ANY)
  fits      E9: L,R vs lambda -> (base,k) by 2-point solve + 3rd-point residual
Statuses: exact_fit | bounded | non_identifiable(+missing experiment)
"""
from __future__ import annotations
import argparse, glob, json, os, sys, itertools
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yxmodel import TimingModel, LMUL_FACTOR  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_traces(pattern):
    out = []
    for f in sorted(glob.glob(pattern)):
        t = json.load(open(f))
        cyc = [e["cycle"] for e in t["entries"] if e["cycle"] is not None]
        if len(cyc) >= 2:
            t["delta"] = cyc[-1] - cyc[0]
        t["_dir"] = os.path.dirname(f)
        out.append(t)
    return out

def lsq_slope(points):
    """points: [(x, y)]; returns slope if points fit y = slope*x + c EXACTLY
    (integer c), else None. Streams with 1-wide cadence may show saturating
    (ceil-like) deltas from same-cycle dual issue; those are reported as
    conflicts upstream and fall back to bounded estimates."""
    if len(points) < 2:
        return None
    pts = sorted(points)
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    if x1 == x0:
        return None
    num, den = y1 - y0, x1 - x0
    if num % den != 0:
        return None
    slope = num // den
    c = y0 - slope * x0
    if any(y != slope * x + c for x, y in pts):
        return None
    return slope

def bounded_slope(points):
    """For saturating streams: slope = ceil((y_max - y_min) / (x_max - x_min))
    as an upper bound plus the observed inter-point modes."""
    pts = sorted(points)
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    if x1 == x0:
        return None, None
    import math
    hi = math.ceil((y1 - y0) / (x1 - x0))
    lo = min((pts[i+1][1] - pts[i][1]) for i in range(len(pts)-1)
             if pts[i+1][0] > pts[i][0])
    return lo, hi

def fit_linear(pairs):
    """pairs: {lmul: value}; solve base + k*lambda; require exactness."""
    if len(pairs) < 2:
        return None, None, "insufficient_points"
    (l1, v1), (l2, v2) = sorted(pairs.items(), key=lambda kv: LMUL_FACTOR[kv[0]])[:2]
    k_num = v2 - v1
    k_den = LMUL_FACTOR[l2] - LMUL_FACTOR[l1]
    if k_num % k_den != 0:
        return None, None, "non_integer_k"
    k = k_num // k_den
    base = v1 - k * LMUL_FACTOR[l1]
    resid = sum(abs(v - (base + k * LMUL_FACTOR[lm])) for lm, v in pairs.items())
    return (base, k), resid, ("exact_fit" if resid == 0 else "approximate")

class Analyzer:
    def __init__(self, results_dir, cfg):
        self.dir = results_dir
        self.m = TimingModel(cfg)
        self.E = defaultdict(list)   # template -> traces

    def ingest(self):
        for t in load_traces(os.path.join(self.dir, "*", "trace.json")):
            self.E[t["template"]].append(t)

    # ------------------------------------------------------------------ E2
    def infer_R(self):
        out = {}
        streams = defaultdict(dict)   # (instr,lm) -> {n: delta}
        for t in self.E["E2_STREAM"]:
            streams[(t["meta"]["instruction"], t["meta"]["lmul"])][t["meta"]["n"]] = t["delta"]
        for key, pts in streams.items():
            slope = lsq_slope(sorted(pts.items()))
            if slope is not None:
                out[key] = dict(value=slope, status="exact_fit", points=dict(pts))
            else:
                lo, hi = bounded_slope(sorted(pts.items()))
                val = None
                if lo == hi:
                    val, st = lo, "exact_fit"
                elif lo is not None and hi is not None and hi - lo == 1:
                    val, st = hi, "bounded(pm1)"
                else:
                    val, st = hi, "bounded"
                out[key] = dict(value=val, status=st, points=dict(pts),
                                lo=lo, hi=hi)
        return out

    # ------------------------------------------------------------------ E3
    def infer_L_chain(self):
        out = {}
        chains = defaultdict(dict)
        for t in self.E["E3_CHAIN"]:
            chains[(t["meta"]["instruction"], t["meta"]["lmul"])][t["meta"]["n"]] = t["delta"]
        for key, pts in chains.items():
            slope = lsq_slope(sorted(pts.items()))
            out[key] = dict(value=slope, status="exact_fit" if slope else "conflict",
                            points=dict(pts))
        return out

    # ------------------------------------------------------------------ E4
    def infer_L_xraw_and_pen(self, L_chain):
        """Default-consumer k-sweep (dep & ctrl) + all-consumer k=0 matrix."""
        sweeps = defaultdict(lambda: defaultdict(dict))  # (p,lm,k) -> {'dep':d,'ctrl':d}
        k0 = {}       # (p,c,lm) -> dep delta at k=0
        for t in self.E["E4_XRAW"]:
            me = t["meta"]; p, c, lm, k = me["producer"], me["consumer"], me["lmul"], me["k"]
            if me["control"]:
                sweeps[(p, c, lm)][k]["ctrl"] = t["delta"]
            else:
                sweeps[(p, c, lm)][k]["dep"] = t["delta"]
                if k == 0:
                    k0[(p, c, lm)] = t["delta"]
        # L(p) from default-consumer sweep: stall(k) = dep(k)-ctrl(k); L+pen = k* + stall(k*)
        L = {}
        KIND = {"vadd_vv": "vector", "vmul_vv": "vector", "vdivu_vv": "vector",
                "vmseq_vv": "mask", "vredsum_vs": "vector", "vslideup_vx": "vector",
                "vcpop_m": "scalar", "viota_m": "vector"}
        default_c = {i: {"vector": "vadd_vv", "mask": "vcpop_m", "scalar": "scalar_add"}[KIND[i]]
                     for i in self.m.instrs}
        L_sweep = {}
        for (p, c, lm), ks in sweeps.items():
            if c != default_c.get(p):
                continue
            stalls = {k: v.get("dep", 10**9) - v.get("ctrl", 0) for k, v in ks.items()
                      if "dep" in v and "ctrl" in v}
            if not stalls:
                continue
            kstar = max(k for k in stalls if stalls[k] > 0) if any(v > 0 for v in stalls.values()) else min(stalls)
            total = kstar + max(0, stalls[kstar]) if stalls[kstar] > 0 else None
            if total is not None:
                L_sweep[(p, lm)] = total
            else:
                # stall vanished at k*; L+pen is in (k*-1's total, k*] bound
                kprev = kstar - 1
                if kprev in stalls:
                    L_sweep[(p, lm)] = kprev + stalls[kprev]  # exact: last stalling k
        # penalty matrix from k=0: pen(p->c) = k0 - 1 - L(p)
        pen = {}
        for (p, c, lm), d in k0.items():
            if (p, lm) in L_sweep:
                pen[(p, c, lm)] = d - 1 - L_sweep[(p, lm)]
        return L_sweep, pen

    # ------------------------------------------------------------------ E5
    def infer_waw(self):
        out = {}
        grouped = defaultdict(dict)
        for t in self.E["E5_WAW"]:
            me = t["meta"]
            grouped[(me["instruction"], me["lmul"], me["d"])][
                "ctrl" if me["control"] else "waw"] = t["delta"]
        spacing = {}
        for (i, lm, d), v in grouped.items():
            if "waw" in v and "ctrl" in v:
                spacing[(i, lm, d)] = v["waw"] - v["ctrl"]
        waw = {}
        by_i = defaultdict(dict)
        for (i, lm, d), s in spacing.items():
            by_i[(i, lm)][d] = s
        for key, dd in by_i.items():
            stall_ds = [d for d, s in dd.items() if s > 0]
            if not stall_ds:
                waw[key] = dict(value=None, status="non_identifiable")
                continue
            dmax = max(stall_ds)
            # spacing = dmax + stall(dmax)
            ctrl_at = {d: s for d, s in dd.items()}
            waw[key] = dict(value=dmax + dd[dmax], status="exact_fit",
                            stall_at=dict(sorted(dd.items())))
        return waw

    # ------------------------------------------------------------------ E6
    def infer_war(self):
        out = {}
        grouped = defaultdict(dict)
        for t in self.E["E6_WAR"]:
            me = t["meta"]
            grouped[(me["reader"], me["writer"], me["lmul"], me["d"])][
                "ctrl" if me["control"] else "war"] = t["delta"]
        rl = {}
        by_r = defaultdict(dict)
        for (r, w, lm, d), v in grouped.items():
            if "war" in v and "ctrl" in v and lm == "m1":
                by_r[(r, w)][d] = v["war"] - v["ctrl"]
        for key, dd in by_r.items():
            ds = [d for d, s in dd.items() if s > 0]
            rl[key] = (max(ds) + 1) if ds else 0   # first d without stall
        return rl

    # ------------------------------------------------------------------ E7
    def infer_pipes(self, R):
        verdicts = {}
        for t in self.E["E7_MIX"]:
            me = t["meta"]; a, b, lm = me["a"], me["b"], me["lmul"]
            slope = t["delta"] / max(1, me["pairs"])
            Ra = R.get((a, "m1"), {}).get("value")
            Rb = R.get((b, "m1"), {}).get("value")
            verdicts[(a, b, lm)] = slope
        return verdicts

    # ------------------------------------------------------------ pipeline
    def run(self):
        R = self.infer_R()
        L_chain = self.infer_L_chain()
        L_xraw, pen = self.infer_L_xraw_and_pen(L_chain)
        waw = self.infer_waw()
        war = self.infer_war()
        verdicts = self.infer_pipes(R)

        # per-instruction assembly
        profile = {}
        for i in self.m.all_classes():
            entry = {"latency": {}, "release": {}, "waw": {}, "status": {}}
            for lm in LMUL_FACTOR:
                Lc = L_chain.get((i, lm), {}).get("value")
                Lx = L_xraw.get((i, lm))
                L = Lc if Lc is not None else Lx
                entry["latency"][lm] = L
                entry["release"][lm] = R.get((i, lm), {}).get("value")
                entry["waw"][lm] = waw.get((i, lm), {}).get("value")
            for field, d in (("latency", entry["latency"]), ("release", entry["release"])):
                fit, resid, status = fit_linear({lm: v for lm, v in d.items() if v is not None})
                entry["status"][field] = dict(fit=fit, residual=resid, status=status,
                                              per_lmul=dict(d))
            profile[i] = entry

        report = dict(profile=profile,
                      penalty_matrix={f"{p}->{c}@{lm}": v for (p, c, lm), v in pen.items()},
                      war_release={f"{r}->{w}": v for (r, w), v in war.items()},
                      e7_slopes={f"{a}+{b}@{lm}": v for (a, b, lm), v in verdicts.items()},
                      ground_truth=self.m.summary_table())
        os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
        json.dump(report, open(os.path.join(ROOT, "results", "analysis_v2.json"), "w"),
                  indent=1, default=str)
        # calibration check vs ground truth
        ok, bad = 0, []
        for i in self.m.all_classes():
            for lm in LMUL_FACTOR:
                for field, getter in (("latency", self.m.L), ("release", self.m.R)):
                    got = profile[i][field][lm]
                    want = getter(i, lm)
                    if got is not None and got != want:
                        bad.append(f"{i}@{lm} {field}: got {got} want {want}")
                    elif got is not None:
                        ok += 1
        print(f"calibration: {ok} exact matches, {len(bad)} mismatches")
        for b in bad[:20]:
            print("  MISMATCH", b)
        return report

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(ROOT, "results"))
    ap.add_argument("--config", default=os.path.join(ROOT, "config", "yushuxin_timing_v2.yaml"))
    a = ap.parse_args()
    an = Analyzer(a.results, a.config)
    an.ingest()
    an.run()
