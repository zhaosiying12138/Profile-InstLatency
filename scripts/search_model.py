#!/usr/bin/env python3
"""Deterministic placeholder parameter search for RVV timing profiles.

The search is deliberately conservative: it fits small integer
`base + k * LMUL` formulas only when enough numeric observations are present.
It never treats the result as calibrated proof.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LMUL_VALUE = {"m1": 1, "m2": 2, "m4": 4, "m8": 8}


@dataclass(frozen=True)
class FormulaCandidate:
    base: int
    k: int
    residual: float


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if text in ("null", "None", "~"):
        return None
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if text.startswith("[") and text.endswith("]"):
        body = text[1:-1].strip()
        if not body:
            return []
        return [parse_scalar(part.strip()) for part in body.split(",")]
    if text.startswith("{") and text.endswith("}"):
        result: dict[str, Any] = {}
        body = text[1:-1].strip()
        if not body:
            return result
        for part in body.split(","):
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            result[key.strip()] = parse_scalar(value)
        return result
    try:
        return int(text, 0)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text.strip("\"'")


def parse_yamlish(path: Path) -> Any:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))

    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, value = line.strip().split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip():
            parent[key.strip()] = parse_scalar(value)
        else:
            child: dict[str, Any] = {}
            parent[key.strip()] = child
            stack.append((indent, child))
    return root


def load_inputs(paths: list[str]) -> list[tuple[Path, Any]]:
    loaded: list[tuple[Path, Any]] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            for child in sorted(path.rglob("*.yaml")) + sorted(path.rglob("*.yml")) + sorted(path.rglob("*.json")):
                loaded.append((child, parse_yamlish(child)))
        elif path.exists():
            loaded.append((path, parse_yamlish(path)))
    return loaded


def walk_scalars(data: Any, prefix: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], Any]]:
    if isinstance(data, dict):
        output: list[tuple[tuple[str, ...], Any]] = []
        for key in sorted(data):
            output.extend(walk_scalars(data[key], prefix + (str(key),)))
        return output
    if isinstance(data, list):
        output = []
        for index, value in enumerate(data):
            output.extend(walk_scalars(value, prefix + (str(index),)))
        return output
    return [(prefix, data)]


def collect_points(loaded: list[tuple[Path, Any]]) -> dict[str, dict[str, dict[str, float]]]:
    """Return field -> instruction -> lmul -> observed value."""
    points: dict[str, dict[str, dict[str, float]]] = {"latency": {}, "release": {}}
    for _path, data in loaded:
        for key_path, value in walk_scalars(data):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            lowered = tuple(part.lower() for part in key_path)
            lmul = next((part for part in lowered if part in LMUL_VALUE), None)
            if lmul is None:
                continue
            instruction = infer_instruction_id(key_path)
            if instruction is None:
                continue
            field = infer_field(lowered)
            if field is None:
                continue
            points.setdefault(field, {}).setdefault(instruction, {})[lmul] = float(value)
    return points


def infer_instruction_id(key_path: tuple[str, ...]) -> str | None:
    for part in key_path:
        if part.startswith("v") and ("_" in part or part in ("vadd", "vmul", "vsll")):
            return part
    return None


def infer_field(lowered_path: tuple[str, ...]) -> str | None:
    joined = ".".join(lowered_path)
    if "release" in joined or "occupancy" in joined or "throughput" in joined:
        return "release"
    if "latency" in joined or "raw" in joined:
        return "latency"
    return None


def fit_formula(points: dict[str, float], max_value: int) -> FormulaCandidate | None:
    numeric_points = [(LMUL_VALUE[key], value) for key, value in sorted(points.items()) if key in LMUL_VALUE]
    if len(numeric_points) < 2:
        return None
    best: FormulaCandidate | None = None
    for base in range(max_value + 1):
        for k in range(max_value + 1):
            residual = sum(abs((base + k * lmul) - observed) for lmul, observed in numeric_points)
            candidate = FormulaCandidate(base, k, residual)
            if best is None or (candidate.residual, candidate.base, candidate.k) < (best.residual, best.base, best.k):
                best = candidate
    return best


def build_report(loaded: list[tuple[Path, Any]], max_value: int) -> dict[str, Any]:
    points = collect_points(loaded)
    instructions = sorted({instr for field in points.values() for instr in field})
    results: dict[str, Any] = {
        "schema_version": 1,
        "status": "placeholder_search",
        "confidence": "low_until_replayed_against_trace_templates",
        "input_files": [path.as_posix() for path, _data in loaded],
        "instructions": {},
        "notes": [
            "Search fits only small integer base_plus_lmul_times_k formulas.",
            "No result is a calibration proof without simulator replay and mismatch review.",
        ],
    }
    for instr in instructions:
        instr_result: dict[str, Any] = {}
        for field in ("latency", "release"):
            field_points = points.get(field, {}).get(instr, {})
            candidate = fit_formula(field_points, max_value)
            if candidate is None:
                instr_result[field] = {
                    "status": "not_enough_data",
                    "observations": field_points,
                }
            else:
                instr_result[field] = {
                    "status": "candidate",
                    "form": "base_plus_lmul_times_k",
                    "base": candidate.base,
                    "k": candidate.k,
                    "absolute_residual": candidate.residual,
                    "observations": field_points,
                }
        results["instructions"][instr] = instr_result
    return results


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Timing Parameter Search",
        "",
        f"Status: {report['status']}",
        f"Confidence: {report['confidence']}",
        "",
        "This is a deterministic placeholder search. It proposes small integer formulas only; it does not prove calibration.",
        "",
        "## Inputs",
        "",
    ]
    input_files = report.get("input_files") or []
    if input_files:
        for path in input_files:
            lines.append(f"- `{path}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Candidates", ""])
    instructions = report.get("instructions", {})
    if not instructions:
        lines.append("No candidate formulas were produced because no numeric LMUL observations were found.")
    else:
        lines.append("| Instruction | Field | Status | Formula | Residual |")
        lines.append("| --- | --- | --- | --- | ---: |")
        for instr in sorted(instructions):
            for field in ("latency", "release"):
                item = instructions[instr][field]
                if item["status"] == "candidate":
                    formula = f"{item['base']} + {item['k']} * LMUL"
                    residual = item["absolute_residual"]
                else:
                    formula = "n/a"
                    residual = "n/a"
                lines.append(f"| `{instr}` | `{field}` | {item['status']} | `{formula}` | {residual} |")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search conservative RVV timing-model candidates.")
    parser.add_argument("--config", action="append", default=[], help="YAML-ish timing config file or directory.")
    parser.add_argument("--profile", action="append", default=[], help="YAML-ish profile file or directory.")
    parser.add_argument("--output", help="Optional output path.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--max-value", type=int, default=32, help="Maximum integer base/k value to enumerate.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    loaded = load_inputs(args.config + args.profile)
    report = build_report(loaded, args.max_value)
    if args.format == "json":
        content = json.dumps(report, indent=2, sort_keys=True) + "\n"
    else:
        content = render_markdown(report)

    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path}")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
