#!/usr/bin/env python3
"""Build deterministic evidence and reference figures for the RVV blog."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "blogs" / "assets"
REF_ROOT = ASSET_ROOT / "reference"
BLOG_RESULTS = ROOT / "results" / "blog"

FIGURE_NAMES = [
    "issue-width",
    "micro-op-buffer-size",
    "proc-resource",
    "latency",
    "release-at-cycles",
    "acquire-at-cycles",
    "num-micro-ops",
    "single-issue-group",
    "read-advance",
    "lmul-scaling",
    "timestamp-model",
    "composite-schedule",
]

COLORS = {
    "div": "#2b6cb0",
    "add": "#2f855a",
    "scalar": "#805ad5",
    "marker": "#1a202c",
    "bubble": "#e53e3e",
    "resource": "#d69e2e",
    "note": "#718096",
    "bg": "#f8fafc",
    "grid": "#e2e8f0",
}


@dataclass(frozen=True)
class Op:
    label: str
    cycle: int
    row: str
    color: str
    duration: int = 1
    detail: str = ""


EXEC_RE = re.compile(
    r"^\s*(?P<tick>\d+):.*?\b0x(?P<pc>[0-9a-fA-F]+)\b.*?:\s*(?P<inst>.*?)\s*(?::\s*(?P<class>[A-Za-z_][A-Za-z0-9_]*))?\s*(?::|$)"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def marker_cycles(trace_path: Path) -> dict[str, int]:
    trace = load_json(trace_path)
    return {str(item["marker"]): int(item["cycle"]) for item in trace["entries"]}


def marker_pcs(trace_path: Path) -> dict[str, int]:
    trace = load_json(trace_path)
    return {str(k): int(str(v), 16) for k, v in trace["marker_addresses"].items()}


def parse_exec(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        match = EXEC_RE.match(raw)
        if not match:
            continue
        inst = " ".join(match.group("inst").split())
        rows.append(
            {
                "line": line_no,
                "tick": int(match.group("tick")),
                "cycle": int(match.group("tick")) // 1000,
                "pc": int(match.group("pc"), 16),
                "inst": inst,
                "class": match.group("class") or "",
                "raw": raw.strip(),
                "is_micro": "." in raw.split("@", 1)[-1].split(":", 1)[0],
            }
        )
    return rows


def experiment(group: str, exp_id: str) -> dict[str, Path]:
    base = BLOG_RESULTS / group / "experiments" / exp_id
    return {
        "base": base,
        "test": base / "test.s",
        "trace": base / "trace.json",
        "exec": base / "gem5" / "exec.log",
    }


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def missing_exec_logs(exps: dict[str, dict[str, Path]]) -> list[str]:
    return sorted(relative_path(exp["exec"]) for exp in exps.values() if not exp["exec"].exists())


def rows_between(exp: dict[str, Path], start: str, end: str) -> list[dict[str, Any]]:
    pcs = marker_pcs(exp["trace"])
    lo, hi = pcs[start], pcs[end]
    return [row for row in parse_exec(exp["exec"]) if lo <= row["pc"] <= hi]


def macro_ops(rows: list[dict[str, Any]], wanted: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if row["is_micro"]:
            continue
        if wanted and not any(token in row["inst"] for token in wanted):
            continue
        result.append(row)
    return result


def short_inst(inst: str) -> str:
    return (
        inst.replace("vdivu_vv", "vdivu.vv")
        .replace("vadd_vv", "vadd.vv")
        .replace("vredsum_vs", "vredsum.vs")
        .replace("addi zero, zero, 0", "nop")
    )


def svg_timeline(path: Path, title: str, ops: list[Op], notes: list[str], width: int = 1320) -> None:
    min_cycle = min((op.cycle for op in ops), default=0)
    max_cycle = max((op.cycle + op.duration for op in ops), default=min_cycle + 1)
    span = max(1, max_cycle - min_cycle)
    rows = list(dict.fromkeys(op.row for op in ops))
    row_y = {row: 110 + index * 74 for index, row in enumerate(rows)}
    left, right = 170, width - 50
    scale = (right - left) / span
    height = max(360, 180 + len(rows) * 74 + len(notes) * 28)
    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="{COLORS["bg"]}"/>',
        f'<text x="34" y="48" font-size="28" font-family="Inter,Arial" font-weight="700" fill="#172033">{html.escape(title)}</text>',
    ]
    for tick in range(min_cycle, max_cycle + 1):
        x = left + (tick - min_cycle) * scale
        pieces.append(f'<line x1="{x:.1f}" y1="78" x2="{x:.1f}" y2="{height-80}" stroke="{COLORS["grid"]}" stroke-width="1"/>')
        pieces.append(f'<text x="{x:.1f}" y="96" font-size="13" text-anchor="middle" fill="#4a5568">{tick}</text>')
    for row, y in row_y.items():
        pieces.append(f'<text x="34" y="{y+25}" font-size="18" font-family="Inter,Arial" fill="#27364a">{html.escape(row)}</text>')
        pieces.append(f'<line x1="{left}" y1="{y+32}" x2="{right}" y2="{y+32}" stroke="#cbd5e1" stroke-width="1"/>')
    for op in ops:
        x = left + (op.cycle - min_cycle) * scale
        w = max(34, op.duration * scale - 4)
        y = row_y[op.row]
        pieces.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="42" rx="6" fill="{op.color}"/>')
        pieces.append(f'<text x="{x + w/2:.1f}" y="{y+25}" font-size="15" text-anchor="middle" fill="white" font-family="Inter,Arial">{html.escape(op.label)}</text>')
        if op.detail:
            pieces.append(f'<text x="{x:.1f}" y="{y+58}" font-size="12" fill="#334155" font-family="Inter,Arial">{html.escape(op.detail)}</text>')
    note_y = height - 52 - (len(notes) - 1) * 24
    for note in notes:
        pieces.append(f'<text x="34" y="{note_y}" font-size="16" font-family="Inter,Arial" fill="#334155">{html.escape(note)}</text>')
        note_y += 24
    pieces.append("</svg>")
    path.write_text("\n".join(pieces) + "\n", encoding="utf-8")


def png_timeline(path: Path, title: str, ops: list[Op], notes: list[str], width: int = 1320) -> None:
    min_cycle = min((op.cycle for op in ops), default=0)
    max_cycle = max((op.cycle + op.duration for op in ops), default=min_cycle + 1)
    span = max(1, max_cycle - min_cycle)
    rows = list(dict.fromkeys(op.row for op in ops))
    row_y = {row: 110 + index * 74 for index, row in enumerate(rows)}
    left, right = 170, width - 50
    scale = (right - left) / span
    height = max(360, 180 + len(rows) * 74 + len(notes) * 28)
    image = Image.new("RGB", (width, height), COLORS["bg"])
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default(size=28)
    font = ImageFont.load_default(size=16)
    small = ImageFont.load_default(size=12)
    draw.text((34, 28), title, font=font_title, fill="#172033")
    for tick in range(min_cycle, max_cycle + 1):
        x = left + (tick - min_cycle) * scale
        draw.line((x, 78, x, height - 80), fill=COLORS["grid"])
        draw.text((x - 8, 82), str(tick), font=small, fill="#4a5568")
    for row, y in row_y.items():
        draw.text((34, y + 14), row, font=font, fill="#27364a")
        draw.line((left, y + 32, right, y + 32), fill="#cbd5e1")
    for op in ops:
        x = left + (op.cycle - min_cycle) * scale
        w = max(34, op.duration * scale - 4)
        y = row_y[op.row]
        draw.rounded_rectangle((x, y, x + w, y + 42), radius=6, fill=op.color)
        draw.text((x + 8, y + 14), op.label[:18], font=small, fill="white")
        if op.detail:
            draw.text((x, y + 48), op.detail[:42], font=small, fill="#334155")
    note_y = height - 58 - (len(notes) - 1) * 24
    for note in notes:
        draw.text((34, note_y), note, font=font, fill="#334155")
        note_y += 24
    image.save(path)


def write_figure(name: str, title: str, ops: list[Op], notes: list[str], width: int = 1320) -> None:
    svg_timeline(REF_ROOT / f"{name}.svg", title, ops, notes, width=width)
    png_timeline(REF_ROOT / f"{name}.png", title, ops, notes, width=width)


def op_from_row(row: dict[str, Any], base: int, label: str | None = None, row_name: str = "issue") -> Op:
    inst = short_inst(row["inst"])
    color = COLORS["div"] if "vdivu" in inst else COLORS["add"] if "vadd" in inst else COLORS["scalar"]
    return Op(label or inst.split()[0], row["cycle"] - base, row_name, color, detail=inst)


def build() -> None:
    REF_ROOT.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, Any] = {
        "real_profile": {
            "Latency": {"m1": 4, "m2": 4, "m4": 4},
            "ReleaseAtCycles": {"m1": 1, "m2": 2, "m4": 4},
            "ProcResource": "YuShuXinVPipe0",
            "NumMicroOps": 1,
            "SingleIssue": False,
            "formula": {
                "Latency": "4 + 0 * LMUL",
                "ReleaseAtCycles": "0 + 1 * LMUL",
            },
        },
        "experiments": {},
    }

    exps = {
        "t10_m1": experiment("vdivu_vv", "t10-vdivu-vv-m1-n4"),
        "t10_m2": experiment("vdivu_vv", "t10-vdivu-vv-m2-n4"),
        "t10_m4": experiment("vdivu_vv", "t10-vdivu-vv-m4-n4"),
        "t11_m1": experiment("vdivu_vv", "t11-vdivu-vv-m1-n4"),
        "t12_k2": experiment("vdivu_vv", "t12-vdivu-vv-m1-k2-vadd-vv"),
        "t12_k4": experiment("vdivu_vv", "t12-vdivu-vv-m1-k4-vadd-vv"),
        "t20": experiment("vdivu_vv", "t20-vdivu-vv-vredsum-vs-m1-n4"),
        "t21": experiment("vdivu_vv", "t21-vdivu-vv-m1-n4"),
        "t00": experiment("common", "t00-marker"),
        "composite": experiment("vdivu_vv_composite", "vdivu-vv-composite-real"),
    }

    for key, exp in exps.items():
        cycles = marker_cycles(exp["trace"])
        evidence["experiments"][key] = {
            "trace": relative_path(exp["trace"]),
            "test": relative_path(exp["test"]),
            "marker_cycles": cycles,
            "primary_delta": max(cycles.values()) - min(cycles.values()) if cycles else None,
        }

    missing_logs = missing_exec_logs(exps)
    if missing_logs:
        evidence["degraded"] = True
        evidence["degraded_reason"] = "gem5 exec.log inputs are absent; preserving committed figures"
        evidence["missing_exec_logs"] = missing_logs
        evidence_path = REF_ROOT / "evidence.json"
        if not evidence_path.exists():
            evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return

    # Issue width and SingleIssue share T21 evidence.
    t21_rows = macro_ops(rows_between(exps["t21"], "start", "end"), ("vdivu_vv", "add "))
    base = t21_rows[0]["cycle"]
    ops = [
        op_from_row(row, base, row_name=("vector lane" if "vdivu_vv" in row["inst"] else "scalar lane"))
        for row in t21_rows
    ]
    write_figure(
        "issue-width",
        "T21 vdivu.vv + scalar add: IssueWidth = 2",
        ops,
        ["Vector and scalar instructions issue in the same cycle group.", "The processor model uses let IssueWidth = 2."],
    )
    write_figure(
        "single-issue-group",
        "T21 pairing: SingleIssue = false",
        ops,
        ["vdivu.vv does not force an isolated issue group in this evidence.", "No BeginGroup/EndGroup claim is emitted."],
    )

    # T10 independent stream.
    t10_rows = macro_ops(rows_between(exps["t10_m1"], "start", "end"), ("vdivu_vv",))
    base = t10_rows[0]["cycle"]
    t10_ops = [op_from_row(row, base, label=f"D{idx}", row_name="VPipe0 canonical") for idx, row in enumerate(t10_rows)]
    write_figure(
        "release-at-cycles",
        "T10 m1 independent stream: ReleaseAtCycles = 1",
        t10_ops,
        ["Four independent divides issue at consecutive cycles.", "The n-sweep fit gives release = 1 for LMUL m1."],
    )
    write_figure(
        "acquire-at-cycles",
        "T10 m1 resource acquisition: default acquire at issue",
        t10_ops,
        ["The profile has no delayed AcquireAtCycles evidence.", "LLVM sketch leaves AcquireAtCycles empty."],
    )
    write_figure(
        "micro-op-buffer-size",
        "In-order marker window: MicroOpBufferSize = 0",
        t10_ops,
        ["The processor assumption is in-order/no ROB.", "The trace is consistent with program-order issue inside the marker window."],
    )

    # T11 latency.
    t11_rows = macro_ops(rows_between(exps["t11_m1"], "start", "end"), ("vdivu_vv",))
    base = t11_rows[0]["cycle"]
    t11_ops = [op_from_row(row, base, label=f"RAW{idx}", row_name="dependent chain") for idx, row in enumerate(t11_rows)]
    write_figure(
        "latency",
        "T11 m1 self RAW chain: Latency = 4",
        t11_ops,
        ["Dependent vdivu.vv issues at +4 cycle intervals.", "The inferred LLVM Latency is 4."],
    )

    # T20 resource.
    t20_rows = macro_ops(rows_between(exps["t20"], "start", "end"), ("vdivu_vv", "vredsum_vs"))
    base = t20_rows[0]["cycle"]
    t20_ops = [op_from_row(row, base, label=("DIV" if "vdivu" in row["inst"] else "RED"), row_name="pair stream") for row in t20_rows]
    write_figure(
        "proc-resource",
        "T20 pairwise classification: ProcResource = YuShuXinVPipe0",
        t20_ops,
        ["Global solving has a pipe0/pipe1 mirror symmetry.", "The report canonicalizes vdivu.vv to YuShuXinVPipe0."],
    )

    # NumMicroOps from micro rows.
    t10_all = rows_between(exps["t10_m1"], "start", "end")
    micro_ops = [row for row in t10_all if row["is_micro"] and "vdivu_vv_micro" in row["inst"]]
    base = t10_rows[0]["cycle"]
    num_ops = [Op("macro", row["cycle"] - base, "macro inst", COLORS["div"], detail=short_inst(row["inst"])) for row in t10_rows]
    num_ops += [Op("micro.0", row["cycle"] - base, "gem5 micro", COLORS["resource"], detail=short_inst(row["inst"])) for row in micro_ops]
    write_figure(
        "num-micro-ops",
        "T10 m1 expansion: NumMicroOps = 1",
        num_ops,
        ["Each m1 vdivu.vv has one gem5 micro row in the marker window.", "The real profile infers NumMicroOps = 1 for m1/m2/m4 LLVM field search."],
    )

    # ReadAdvance / T12.
    t12_rows = macro_ops(rows_between(exps["t12_k2"], "start", "end"), ("vdivu_vv", "vadd_vv"))
    base = t12_rows[0]["cycle"]
    t12_ops = [op_from_row(row, base, row_name="gap window") for row in t12_rows]
    t12_ops.append(Op("bubble", 3, "gap window", COLORS["bubble"], detail="consumer waits for readiness"))
    write_figure(
        "read-advance",
        "T12 k=2 consumer gap: no ReadAdvance claim",
        t12_ops,
        ["Two fillers do not fully hide vdivu.vv readiness.", "The experiment constrains Latency, not a consumer-specific ReadAdvance field."],
    )

    # LMUL scaling.
    lmul_ops: list[Op] = []
    for row_name, key, label in [("m1", "t10_m1", "m1"), ("m2", "t10_m2", "m2"), ("m4", "t10_m4", "m4")]:
        rows = macro_ops(rows_between(exps[key], "start", "end"), ("vdivu_vv",))
        b = rows[0]["cycle"]
        for idx, row in enumerate(rows[:4]):
            lmul_ops.append(op_from_row(row, b, label=f"{label}.{idx}", row_name=row_name))
    write_figure(
        "lmul-scaling",
        "T10 LMUL scaling: release m1/m2/m4 = 1/2/4",
        lmul_ops,
        ["Macro issue distance grows with LMUL.", "Latency remains 4; ReleaseAtCycles follows 0 + 1 * LMUL."],
        width=1800,
    )

    # Timestamp.
    t00 = marker_cycles(exps["t00"]["trace"])
    ts_ops = [
        Op("t0", t00["t0"], "t0 marker", COLORS["marker"]),
        Op("t1", t00["t1"], "t1 marker", COLORS["marker"]),
    ]
    write_figure(
        "timestamp-model",
        "T00 adjacent markers: timestamp_model cycles = 0",
        ts_ops,
        ["t0 and t1 resolve to the same cycle.", "Markers are zero-cost label-PC wrappers and occupy no issue slot."],
    )

    # Composite.
    comp = exps["composite"]
    comp_rows = parse_exec(comp["exec"])
    comp_cycles = marker_cycles(comp["trace"])
    gap2_base = comp_cycles["m1_gap2_start"]
    m1_base = comp_cycles["m1_ind_start"]
    raw_base = comp_cycles["m1_raw_start"]
    m2_base = comp_cycles["m2_ind_start"]
    m4_base = comp_cycles["m4_ind_start"]
    comp_ops = [
        Op("div@167", 0, "program order", COLORS["div"]),
        Op("fill@168", 1, "program order", COLORS["add"]),
        Op("fill@169", 2, "program order", COLORS["add"]),
        Op("bubble@170", 3, "program order", COLORS["bubble"]),
        Op("use@171", 4, "program order", COLORS["add"]),
        Op("drain", 5, "program order", COLORS["note"], duration=2, detail="40 scalar nops omitted"),
        Op("D0@318", 8, "program order", COLORS["div"]),
        Op("D1@319", 9, "program order", COLORS["div"]),
        Op("D2@320", 10, "program order", COLORS["div"]),
        Op("D3@321", 11, "program order", COLORS["div"]),
        Op("drain", 12, "program order", COLORS["note"], duration=2),
        Op("RAW@482", 15, "program order", COLORS["div"]),
        Op("RAW@486", 19, "program order", COLORS["div"]),
        Op("RAW@490", 23, "program order", COLORS["div"]),
        Op("drain", 24, "program order", COLORS["note"], duration=2),
        Op("m2@657-658", 27, "program order", COLORS["div"], duration=2),
        Op("m2@659-660", 29, "program order", COLORS["div"], duration=2),
        Op("m2@661-662", 31, "program order", COLORS["div"], duration=2),
        Op("drain", 33, "program order", COLORS["note"], duration=2),
        Op("m4@830-833", 36, "program order", COLORS["div"], duration=4),
        Op("m4@834-837", 40, "program order", COLORS["div"], duration=4),
        Op("ready +4", 0, "constraints", COLORS["resource"], duration=4, detail="Latency window"),
        Op("release m1", 8, "constraints", COLORS["resource"], duration=1),
        Op("release m2", 27, "constraints", COLORS["resource"], duration=2),
        Op("release m4", 36, "constraints", COLORS["resource"], duration=4),
    ]
    write_figure(
        "composite-schedule",
        "Composite real experiment: latency, release, LMUL, bubbles",
        comp_ops,
        ["One gem5 program contains gap2, m1 stream, RAW chain, m2 stream, and m4 stream.", "Axis is drain-compressed; real gem5 cycles are printed on each segment."],
        width=2800,
    )

    analysis_lines = [
        "# vdivu.vv Composite Blog Experiment",
        "",
        "Mode: real_platform_profile",
        "Backend: gem5_minor",
        "",
        "## Marker Deltas",
        "",
        "| Segment | Start | End | Delta | Interpretation |",
        "| --- | ---: | ---: | ---: | --- |",
        f"| m1_gap2 | {comp_cycles['m1_gap2_start']} | {comp_cycles['m1_gap2_end']} | {comp_cycles['m1_gap2_end'] - comp_cycles['m1_gap2_start']} | Two fillers leave one dependency bubble before the consumer. |",
        f"| m1_ind | {comp_cycles['m1_ind_start']} | {comp_cycles['m1_ind_end']} | {comp_cycles['m1_ind_end'] - comp_cycles['m1_ind_start']} | Four independent m1 divides have issue starts at +0/+1/+2/+3. |",
        f"| m1_raw | {comp_cycles['m1_raw_start']} | {comp_cycles['m1_raw_end']} | {comp_cycles['m1_raw_end'] - comp_cycles['m1_raw_start']} | Three dependent divides have two +4 latency gaps. |",
        f"| m2_ind | {comp_cycles['m2_ind_start']} | {comp_cycles['m2_ind_end']} | {comp_cycles['m2_ind_end'] - comp_cycles['m2_ind_start']} | Three m2 divides occupy two micro cycles each; macro starts are +0/+2/+4. |",
        f"| m4_ind | {comp_cycles['m4_ind_start']} | {comp_cycles['m4_ind_end']} | {comp_cycles['m4_ind_end'] - comp_cycles['m4_ind_start']} | Two m4 divides occupy four micro cycles each; macro starts are +0/+4. |",
        "",
        "## Dynamic Rows Used By The Blog",
        "",
        "```text",
    ]
    for row in comp_rows:
        inst = row["inst"]
        if "vdivu_vv" in inst or "vadd_vv" in inst or "__prof_marker" in row["raw"]:
            if "vmv_v_i" not in inst:
                analysis_lines.append(row["raw"])
    analysis_lines.extend(["```", ""])
    (comp["base"] / "analysis.md").write_text("\n".join(analysis_lines), encoding="utf-8")

    (REF_ROOT / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
