#!/usr/bin/env python3
"""Search deterministic RVV timing formulas from generated profiles.

The search consumes ``results/<instruction>/profile.yaml`` files and fits
small integer ``base + k * LMUL`` formulas for LLVM latency and
ReleaseAtCycles.  It is stdlib-only and does not treat approximate fits as
calibration proof.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LMUL_ORDER = ("m1", "m2", "m4")
LMUL_VALUE = {"m1": 1, "m2": 2, "m4": 4, "m8": 8}


@dataclass(frozen=True)
class FormulaCandidate:
    base: int
    k: int
    residual: float


def parse_scalar(text: str) -> Any:
    text = text.strip()
    if text in ("", "null", "None", "~"):
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
        body = text[1:-1].strip()
        if not body:
            return {}
        result: dict[str, Any] = {}
        for part in body.split(","):
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            result[str(parse_scalar(key.strip()))] = parse_scalar(value.strip())
        return result
    try:
        return int(text, 0)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text.strip("\"'")


def parse_yamlish(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

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
        clean_key = str(parse_scalar(key.strip()))
        if value.strip():
            parent[clean_key] = parse_scalar(value)
            continue
        child: dict[str, Any] = {}
        parent[clean_key] = child
        stack.append((indent, child))
    return root


def int_or_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(int(value, 0))
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return None
    return None


def profile_files_from_path(raw: str) -> list[Path]:
    path = Path(raw)
    if path.is_dir():
        return sorted(path.rglob("profile.yaml"), key=lambda item: item.as_posix())
    if path.exists():
        return [path]
    return []


def load_profiles(paths: list[str]) -> list[tuple[Path, dict[str, Any]]]:
    loaded: list[tuple[Path, dict[str, Any]]] = []
    for raw in paths:
        for path in profile_files_from_path(raw):
            loaded.append((path, parse_yamlish(path)))
    return loaded


def load_configs(paths: list[str]) -> list[tuple[Path, dict[str, Any]]]:
    loaded: list[tuple[Path, dict[str, Any]]] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            candidates = sorted(path.rglob("*.yaml"), key=lambda item: item.as_posix())
        elif path.exists():
            candidates = [path]
        else:
            candidates = []
        for candidate in candidates:
            loaded.append((candidate, parse_yamlish(candidate)))
    return loaded


def nested_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def collect_profile_points(loaded: list[tuple[Path, dict[str, Any]]]) -> dict[str, dict[str, dict[str, float]]]:
    """Return field -> instruction -> lmul -> observed value."""

    points: dict[str, dict[str, dict[str, float]]] = {"latency": {}, "release": {}}
    for _path, profile in loaded:
        instruction = nested_get(profile, ("instruction", "id"))
        if not instruction:
            continue
        measurements = profile.get("measurements")
        if not isinstance(measurements, dict):
            continue
        for lmul in LMUL_ORDER:
            lmul_measurement = measurements.get(lmul)
            if not isinstance(lmul_measurement, dict):
                continue
            latency = int_or_float(nested_get(lmul_measurement, ("llvm", "latency", "value")))
            release = int_or_float(nested_get(lmul_measurement, ("llvm", "release_at_cycles", "value")))
            if latency is not None:
                points["latency"].setdefault(str(instruction), {})[lmul] = latency
            if release is not None:
                points["release"].setdefault(str(instruction), {})[lmul] = release
    return points


def fit_formula(points: dict[str, float], max_value: int) -> FormulaCandidate | None:
    numeric_points = [(LMUL_VALUE[key], value) for key, value in points.items() if key in LMUL_VALUE]
    if len(numeric_points) < 2:
        return None
    best: FormulaCandidate | None = None
    for base in range(max_value + 1):
        for k in range(max_value + 1):
            residual = sum(abs((base + k * lmul) - observed) for lmul, observed in numeric_points)
            candidate = FormulaCandidate(base, k, residual)
            if best is None or (candidate.residual, candidate.base, candidate.k) < (
                best.residual,
                best.base,
                best.k,
            ):
                best = candidate
    return best


def build_report(
    profiles: list[tuple[Path, dict[str, Any]]],
    configs: list[tuple[Path, dict[str, Any]]],
    max_value: int,
) -> dict[str, Any]:
    points = collect_profile_points(profiles)
    instructions = sorted({instr for field in points.values() for instr in field})
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "profile_parameter_search",
        "formula_form": "base_plus_lmul_times_k",
        "source_profiles": [path.as_posix() for path, _data in profiles],
        "config_files": [path.as_posix() for path, _data in configs],
        "instructions": {},
        "notes": [
            "Search reads generated profile.yaml files, not raw trace placeholders.",
            "Exact zero-residual fits can be compared by the synthetic calibration gate.",
        ],
    }
    for instr in instructions:
        instr_result: dict[str, Any] = {}
        for field in ("latency", "release"):
            observations = points.get(field, {}).get(instr, {})
            candidate = fit_formula(observations, max_value)
            if candidate is None:
                instr_result[field] = {
                    "status": "not_enough_data",
                    "observations": observations,
                }
                continue
            residual = int(candidate.residual) if float(candidate.residual).is_integer() else candidate.residual
            instr_result[field] = {
                "status": "exact_fit" if candidate.residual == 0 else "approximate_fit",
                "form": "base_plus_lmul_times_k",
                "base": candidate.base,
                "k": candidate.k,
                "absolute_residual": residual,
                "observations": observations,
            }
        report["instructions"][instr] = instr_result
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Timing Parameter Search",
        "",
        f"Status: {report['status']}",
        f"Formula form: `{report['formula_form']}`",
        "",
        "## Inputs",
        "",
    ]
    profiles = report.get("source_profiles") or []
    if profiles:
        for path in profiles:
            lines.append(f"- `{path}`")
    else:
        lines.append("- no profile.yaml files found")

    lines.extend(["", "## Candidates", ""])
    instructions = report.get("instructions", {})
    if not instructions:
        lines.append("No candidate formulas were produced because no profile measurements were found.")
    else:
        lines.append("| Instruction | Field | Status | Formula | Residual |")
        lines.append("| --- | --- | --- | --- | ---: |")
        for instr in sorted(instructions):
            for field in ("latency", "release"):
                item = instructions[instr][field]
                if item["status"] in ("exact_fit", "approximate_fit"):
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
    parser.add_argument("--profile", action="append", default=[], help="Profile file or directory containing profile.yaml files.")
    parser.add_argument("--output", help="Optional output path.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--max-value", type=int, default=128, help="Maximum integer base/k value to enumerate.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profiles = load_profiles(args.profile)
    configs = load_configs(args.config)
    report = build_report(profiles, configs, args.max_value)
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
