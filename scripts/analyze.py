#!/usr/bin/env python3
"""Analyze RVV profiling marker traces.

This is intentionally stdlib-only. It accepts the result-tree shape from
docs/plan.md and produces deterministic, conservative analysis notes from any
trace.json files that already exist.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


KNOWN_MARKER_PAIRS = (
    ("t0", "t1"),
    ("before", "after"),
    ("start", "end"),
    ("begin", "end"),
)


@dataclass(frozen=True)
class Marker:
    name: str
    cycle: int
    index: int
    pc: str | None = None


@dataclass(frozen=True)
class ExperimentAnalysis:
    trace_path: Path
    experiment_id: str
    markers: tuple[Marker, ...]
    adjacent_deltas: tuple[tuple[str, str, int], ...]
    named_deltas: tuple[tuple[str, str, int], ...]
    warnings: tuple[str, ...]

    @property
    def corrected_primary_delta(self) -> int | None:
        if self.named_deltas:
            return self.named_deltas[0][2]
        if self.adjacent_deltas:
            return self.adjacent_deltas[-1][2]
        return None


def load_trace(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return [entry for entry in data if isinstance(entry, dict)]
    if isinstance(data, dict):
        for key in ("trace", "events", "markers", "entries"):
            value = data.get(key)
            if isinstance(value, list):
                return [entry for entry in value if isinstance(entry, dict)]
    raise ValueError(f"{path}: expected a list or an object with trace/events/markers")


def marker_name(entry: dict[str, Any], fallback: str) -> str:
    for key in ("marker", "label", "name"):
        value = entry.get(key)
        if value is not None:
            return str(value)
    return fallback


def marker_cycle(entry: dict[str, Any]) -> int | None:
    for key in ("cycle", "cycles", "tick"):
        value = entry.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value, 0)
            except ValueError:
                continue
    return None


def extract_markers(entries: Iterable[dict[str, Any]]) -> tuple[Marker, ...]:
    markers: list[Marker] = []
    for index, entry in enumerate(entries):
        cycle = marker_cycle(entry)
        if cycle is None:
            continue
        pc_value = entry.get("pc")
        pc = str(pc_value) if pc_value is not None else None
        markers.append(Marker(marker_name(entry, f"marker_{index}"), cycle, index, pc))
    return tuple(markers)


def infer_experiment_id(trace_path: Path, entries: list[dict[str, Any]]) -> str:
    for entry in entries:
        value = entry.get("experiment_id")
        if value:
            return str(value)
    return trace_path.parent.name


def analyze_trace(trace_path: Path) -> ExperimentAnalysis:
    entries = load_trace(trace_path)
    markers = extract_markers(entries)
    warnings: list[str] = []
    if not markers:
        warnings.append("trace contains no marker entries with numeric cycles")

    adjacent: list[tuple[str, str, int]] = []
    for left, right in zip(markers, markers[1:]):
        delta = right.cycle - left.cycle
        adjacent.append((left.name, right.name, delta))
        if delta < 0:
            warnings.append(f"marker cycles decrease from {left.name} to {right.name}")

    by_name: dict[str, Marker] = {}
    for marker in markers:
        by_name.setdefault(marker.name, marker)
    named: list[tuple[str, str, int]] = []
    for left_name, right_name in KNOWN_MARKER_PAIRS:
        left = by_name.get(left_name)
        right = by_name.get(right_name)
        if left is not None and right is not None:
            named.append((left_name, right_name, right.cycle - left.cycle))

    return ExperimentAnalysis(
        trace_path=trace_path,
        experiment_id=infer_experiment_id(trace_path, entries),
        markers=markers,
        adjacent_deltas=tuple(adjacent),
        named_deltas=tuple(named),
        warnings=tuple(warnings),
    )


def render_experiment_markdown(analysis: ExperimentAnalysis) -> str:
    lines = [
        "# Experiment Analysis",
        "",
        "Status: preliminary analyzer output.",
        "",
        f"- Trace: `{analysis.trace_path.as_posix()}`",
        f"- Experiment ID: `{analysis.experiment_id}`",
        f"- Marker count: {len(analysis.markers)}",
    ]
    primary = analysis.corrected_primary_delta
    if primary is None:
        lines.append("- Primary delta: not available")
    else:
        lines.append(f"- Primary delta: {primary} cycles")

    lines.extend(["", "## Marker Deltas", ""])
    if analysis.named_deltas:
        lines.append("| From | To | Delta cycles |")
        lines.append("| --- | --- | ---: |")
        for left, right, delta in analysis.named_deltas:
            lines.append(f"| `{left}` | `{right}` | {delta} |")
    elif analysis.adjacent_deltas:
        lines.append("| From | To | Delta cycles |")
        lines.append("| --- | --- | ---: |")
        for left, right, delta in analysis.adjacent_deltas:
            lines.append(f"| `{left}` | `{right}` | {delta} |")
    else:
        lines.append("No usable marker deltas were found.")

    lines.extend(["", "## Confidence", ""])
    lines.append(
        "This file records measured marker deltas only. Throughput, RAW latency, "
        "pipe affinity, and LLVM schedule fields require template-aware fitting "
        "and parameter-search confirmation before they should be treated as inferred."
    )

    if analysis.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in analysis.warnings:
            lines.append(f"- {warning}")

    return "\n".join(lines) + "\n"


def render_aggregate(analyses: list[ExperimentAnalysis], root: Path) -> str:
    lines = [
        "# Experiment Quality Report",
        "",
        "Preliminary status: analyzer scaffold output.",
        "",
        f"Mode: not selected by analyzer; expected values are `synthetic_calibration` or `real_platform_profile`.",
        f"Result root: `{root.as_posix()}`",
        f"Trace files analyzed: {len(analyses)}",
        "",
        "## Coverage",
        "",
    ]
    if not analyses:
        lines.append("No `trace.json` files were found. Coverage is therefore zero.")
    else:
        lines.append("| Experiment | Trace | Marker count | Primary delta | Warnings |")
        lines.append("| --- | --- | ---: | ---: | --- |")
        for item in sorted(analyses, key=lambda item: item.trace_path.as_posix()):
            primary = item.corrected_primary_delta
            primary_text = "n/a" if primary is None else str(primary)
            warning_text = "; ".join(item.warnings) if item.warnings else "none"
            lines.append(
                f"| `{item.experiment_id}` | `{item.trace_path.as_posix()}` | "
                f"{len(item.markers)} | {primary_text} | {warning_text} |"
            )

    primary_values = [item.corrected_primary_delta for item in analyses]
    numeric_values = [value for value in primary_values if value is not None]
    lines.extend(["", "## Stability", ""])
    if numeric_values:
        lines.append(f"Primary delta mean: {mean(numeric_values):.3f} cycles.")
        lines.append("Repeated-run stability is not claimed until repeat groups are present.")
    else:
        lines.append("No numeric primary deltas are available for stability analysis.")

    lines.extend(["", "## Confidence", ""])
    lines.append(
        "Confidence remains preliminary. The analyzer does not compare against "
        "golden values and does not claim LLVM-facing schedule fields on its own."
    )
    lines.append(
        "For `real_platform_profile`, stopping must be based on coverage, stability, "
        "confidence, documented assumptions, conflict resolution, and explicit human approval."
    )

    lines.extend(["", "## Assumptions", ""])
    lines.append("- Marker entries use numeric `cycle`, `cycles`, or `tick` fields.")
    lines.append("- Adjacent marker deltas are useful only after timestamp baseline validation.")
    lines.append("- Template IDs and operand classes are required before field-level inference.")
    return "\n".join(lines) + "\n"


def find_traces(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("**/experiments/**/trace.json"), key=lambda path: path.as_posix())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze RVV marker trace JSON files.")
    parser.add_argument("--all", action="store_true", help="Accepted for the plan's one-command flow.")
    parser.add_argument("--root", default="results", help="Result root to scan.")
    parser.add_argument(
        "--aggregate",
        default="results/common/experiment_quality.md",
        help="Aggregate report path.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without changing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    trace_paths = find_traces(root)
    analyses = [analyze_trace(path) for path in trace_paths]

    writes: list[tuple[Path, str]] = []
    for item in analyses:
        writes.append((item.trace_path.parent / "analysis.md", render_experiment_markdown(item)))
    writes.append((Path(args.aggregate), render_aggregate(analyses, root)))

    if args.dry_run:
        for path, _content in writes:
            print(f"would write {path}")
        return 0

    for path, content in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
