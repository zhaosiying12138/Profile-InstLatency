#!/usr/bin/env python3
"""Analyze RVV profiling traces and synthesize LLVM-facing profiles.

The analyzer is stdlib-only and intentionally conservative.  Synthetic
dry-run traces may carry configured timing metadata; when present, this script
records that metadata as synthetic calibration evidence and compares claimed
fields against ``config/rvv_timing_model.yaml``.  Fields not identifiable from
the first synthetic backend are left explicit and unclaimed.
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

LMUL_ORDER = ("m1", "m2", "m4")
LMUL_VALUE = {"m1": 1, "m2": 2, "m4": 4, "m8": 8}
PIPE_RESOURCE = {
    "any": "YuShuXinAnyVPipe",
    "pipe0": "YuShuXinVPipe0",
    "pipe1": "YuShuXinVPipe1",
}


@dataclass(frozen=True)
class Marker:
    name: str
    cycle: int
    index: int
    pc: str | None = None


@dataclass(frozen=True)
class ExperimentAnalysis:
    trace_path: Path
    experiment_path: Path | None
    experiment_id: str
    template_id: str
    mode: str
    marker_baseline_cycles: int
    instruction_id: str | None
    asm: str | None
    llvm_sched_write: str | None
    lmul: str | None
    synthetic: dict[str, Any]
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
    """Parse the simple YAML subset used by this repository's metadata."""

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


def render_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(render_scalar(item) for item in value) + "]"
    if isinstance(value, dict) and not value:
        return "{}"
    return json.dumps(str(value))


def render_yaml(data: dict[str, Any], indent: int = 0) -> str:
    lines: list[str] = []
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict) and value:
            lines.append(f"{prefix}{key}:")
            lines.append(render_yaml(value, indent + 1))
        else:
            lines.append(f"{prefix}{key}: {render_scalar(value)}")
    return "\n".join(lines)


def load_trace_document(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return {"entries": [entry for entry in data if isinstance(entry, dict)]}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object or list")
    for key in ("entries", "trace", "events", "markers"):
        value = data.get(key)
        if isinstance(value, list):
            data = dict(data)
            data["entries"] = [entry for entry in value if isinstance(entry, dict)]
            return data
    raise ValueError(f"{path}: expected an entries/trace/events/markers list")


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


def nested_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def first_value(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            return None
    return None


def trace_metadata(trace_doc: dict[str, Any]) -> dict[str, Any]:
    metadata = trace_doc.get("metadata")
    synthetic = trace_doc.get("synthetic")
    result: dict[str, Any] = {}
    if isinstance(metadata, dict):
        result.update(metadata)
        nested_synthetic = metadata.get("synthetic")
        if isinstance(nested_synthetic, dict):
            result.setdefault("synthetic", nested_synthetic)
    if isinstance(synthetic, dict):
        result["synthetic"] = synthetic
    return result


def metadata_value(
    trace_doc: dict[str, Any],
    experiment_doc: dict[str, Any],
    key: str,
    experiment_path: tuple[str, ...] = (),
) -> Any:
    metadata = trace_metadata(trace_doc)
    synthetic = metadata.get("synthetic") if isinstance(metadata.get("synthetic"), dict) else {}
    return first_value(
        synthetic.get(key) if isinstance(synthetic, dict) else None,
        metadata.get(key),
        trace_doc.get(key),
        nested_get(experiment_doc, experiment_path) if experiment_path else experiment_doc.get(key),
    )


def analyze_trace(trace_path: Path) -> ExperimentAnalysis:
    trace_doc = load_trace_document(trace_path)
    experiment_path = trace_path.with_name("experiment.yaml")
    experiment_doc = parse_yamlish(experiment_path) if experiment_path.exists() else {}
    entries = trace_doc.get("entries", [])
    markers = extract_markers(entries if isinstance(entries, list) else [])
    warnings: list[str] = []
    if not markers:
        warnings.append("trace contains no marker entries with numeric cycles")

    baseline = int_or_none(trace_doc.get("marker_baseline_cycles")) or 0
    adjacent: list[tuple[str, str, int]] = []
    for left, right in zip(markers, markers[1:]):
        delta = right.cycle - left.cycle - baseline
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
            named.append((left_name, right_name, right.cycle - left.cycle - baseline))

    synthetic = trace_metadata(trace_doc).get("synthetic")
    if not isinstance(synthetic, dict):
        synthetic = {}

    instruction_doc = experiment_doc.get("instruction") if isinstance(experiment_doc.get("instruction"), dict) else {}
    experiment_id = str(
        first_value(
            trace_doc.get("experiment_id"),
            experiment_doc.get("experiment_id"),
            next((entry.get("experiment_id") for entry in entries if isinstance(entry, dict) and entry.get("experiment_id")), None)
            if isinstance(entries, list)
            else None,
            trace_path.parent.name,
        )
    )
    template_id = str(first_value(trace_doc.get("template_id"), experiment_doc.get("template_id"), "unknown"))
    instruction_id = metadata_value(trace_doc, experiment_doc, "instruction_id", ("instruction", "id"))
    lmul = metadata_value(trace_doc, experiment_doc, "lmul")
    asm = first_value(instruction_doc.get("asm") if isinstance(instruction_doc, dict) else None, synthetic.get("asm"))
    llvm_sched_write = first_value(
        instruction_doc.get("llvm_sched_write") if isinstance(instruction_doc, dict) else None,
        trace_doc.get("llvm_sched_write"),
    )
    mode = str(first_value(trace_doc.get("mode"), "unknown"))

    return ExperimentAnalysis(
        trace_path=trace_path,
        experiment_path=experiment_path if experiment_path.exists() else None,
        experiment_id=experiment_id,
        template_id=template_id,
        mode=mode,
        marker_baseline_cycles=baseline,
        instruction_id=str(instruction_id) if instruction_id is not None else None,
        asm=str(asm) if asm is not None else None,
        llvm_sched_write=str(llvm_sched_write) if llvm_sched_write is not None else None,
        lmul=str(lmul) if lmul is not None else None,
        synthetic=dict(synthetic),
        markers=markers,
        adjacent_deltas=tuple(adjacent),
        named_deltas=tuple(named),
        warnings=tuple(warnings),
    )


def evidence_for(item: ExperimentAnalysis) -> list[str]:
    return [f"{item.experiment_id} @ {item.trace_path.as_posix()}"]


def synthetic_int(item: ExperimentAnalysis, key: str) -> int | None:
    return int_or_none(item.synthetic.get(key))


def resource_for_pipe(pipe: str | None) -> str | None:
    if pipe is None:
        return None
    return PIPE_RESOURCE.get(pipe, pipe)


def field_record(
    value: Any,
    confidence: str,
    evidence: list[str],
    *,
    claimed: bool,
    identifiable: bool = True,
    reason: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "value": value,
        "confidence": confidence,
        "claimed": claimed,
        "identifiable": identifiable,
        "evidence": evidence,
    }
    if reason:
        record["reason"] = reason
    return record


def fit_formula(points: dict[str, int], max_value: int = 128) -> dict[str, Any]:
    numeric_points = [(LMUL_VALUE[lmul], value) for lmul, value in points.items() if lmul in LMUL_VALUE]
    evidence_lmuls = [lmul for lmul in LMUL_ORDER if lmul in points]
    if len(numeric_points) < 2:
        return {
            "form": "base_plus_lmul_times_k",
            "base": None,
            "k": None,
            "residual": None,
            "status": "not_enough_data",
            "claimed": False,
            "evidence_lmul": evidence_lmuls,
        }
    best: tuple[float, int, int] | None = None
    for base in range(max_value + 1):
        for k in range(max_value + 1):
            residual = sum(abs((base + k * lmul_value) - observed) for lmul_value, observed in numeric_points)
            candidate = (float(residual), base, k)
            if best is None or candidate < best:
                best = candidate
    assert best is not None
    residual, base, k = best
    return {
        "form": "base_plus_lmul_times_k",
        "base": base,
        "k": k,
        "residual": int(residual) if residual.is_integer() else residual,
        "status": "exact_fit" if residual == 0 else "approximate_fit",
        "claimed": residual == 0,
        "evidence_lmul": evidence_lmuls,
    }


def build_profile(
    instruction_id: str,
    analyses: list[ExperimentAnalysis],
    config_instr: dict[str, Any] | None,
) -> dict[str, Any]:
    by_lmul = {item.lmul: item for item in analyses if item.lmul in LMUL_ORDER}
    first = next(iter(by_lmul.values()), None)
    asm = first.asm if first and first.asm else (config_instr or {}).get("asm")
    sched_write = first.llvm_sched_write if first and first.llvm_sched_write else None

    measurements: dict[str, Any] = {}
    latency_points: dict[str, int] = {}
    release_points: dict[str, int] = {}
    formula_evidence: list[str] = []

    for lmul in LMUL_ORDER:
        item = by_lmul.get(lmul)
        if item is None:
            measurements[lmul] = {
                "llvm": {
                    "proc_resource": field_record(None, "missing_trace", [], claimed=False, identifiable=False),
                    "resource_group": field_record(None, "missing_trace", [], claimed=False, identifiable=False),
                    "latency": field_record(None, "missing_trace", [], claimed=False, identifiable=False),
                    "release_at_cycles": field_record(None, "missing_trace", [], claimed=False, identifiable=False),
                    "acquire_at_cycles": field_record([], "assumed_default", [], claimed=False),
                    "num_micro_ops": field_record(None, "not_identifiable", [], claimed=False, identifiable=False),
                    "single_issue": field_record(None, "not_identifiable", [], claimed=False, identifiable=False),
                    "read_advance": field_record(None, "not_identifiable", [], claimed=False, identifiable=False),
                },
                "hardware_interpretation": {
                    "issue_delay_cycles": field_record(None, "missing_trace", [], claimed=False, identifiable=False),
                    "execute_latency_cycles": field_record(None, "missing_trace", [], claimed=False, identifiable=False),
                    "writeback_latency_cycles": field_record(
                        None,
                        "not_identifiable",
                        [],
                        claimed=False,
                        identifiable=False,
                        reason="Marker traces observe scheduler-visible readiness, not a separate physical writeback stage.",
                    ),
                    "resource_occupancy_cycles": field_record(None, "missing_trace", [], claimed=False, identifiable=False),
                },
            }
            continue

        evidence = evidence_for(item)
        formula_evidence.extend(evidence)
        latency = synthetic_int(item, "latency_cycles")
        release = synthetic_int(item, "release_cycles")
        measured_delta = synthetic_int(item, "measured_delta_cycles")
        if latency is None and item.template_id == "T01_DECODE_EXEC_KILLCHECK":
            latency = item.corrected_primary_delta
        pipe = item.synthetic.get("pipe")
        pipe_text = str(pipe) if pipe is not None else None
        resource = resource_for_pipe(pipe_text)
        if latency is not None:
            latency_points[lmul] = latency
        if release is not None:
            release_points[lmul] = release

        measurements[lmul] = {
            "llvm": {
                "proc_resource": field_record(resource, "synthetic_trace", evidence, claimed=resource is not None),
                "resource_group": field_record(resource, "synthetic_trace", evidence, claimed=resource is not None),
                "pipe_affinity": field_record(pipe_text, "synthetic_trace", evidence, claimed=pipe_text is not None),
                "latency": field_record(latency, "synthetic_trace", evidence, claimed=latency is not None),
                "release_at_cycles": field_record(release, "synthetic_trace", evidence, claimed=release is not None),
                "acquire_at_cycles": field_record([], "assumed_default", [], claimed=False),
                "num_micro_ops": field_record(
                    1,
                    "assumed_until_pairing_probe",
                    [],
                    claimed=False,
                    identifiable=False,
                    reason="The first synthetic backend does not decompose scheduler writes into micro-ops.",
                ),
                "single_issue": field_record(
                    False,
                    "assumed_until_pairing_probe",
                    [],
                    claimed=False,
                    identifiable=False,
                    reason="No pairwise issue-template evidence is present in the current synthetic trace set.",
                ),
                "read_advance": field_record(
                    None,
                    "not_identifiable",
                    [],
                    claimed=False,
                    identifiable=False,
                    reason="Consumer-specific bypass evidence is outside the current synthetic trace claims.",
                ),
            },
            "hardware_interpretation": {
                "issue_delay_cycles": field_record(
                    None,
                    "not_identifiable",
                    evidence,
                    claimed=False,
                    identifiable=False,
                    reason="Current synthetic traces do not split issue delay from execution latency.",
                ),
                "execute_latency_cycles": field_record(
                    measured_delta if measured_delta is not None else latency,
                    "synthetic_trace",
                    evidence,
                    claimed=False,
                    identifiable=True,
                ),
                "writeback_latency_cycles": field_record(
                    None,
                    "not_identifiable",
                    evidence,
                    claimed=False,
                    identifiable=False,
                    reason="LLVM/gem5 marker experiments observe producer-consumer readiness, not a separate physical writeback stage.",
                ),
                "resource_occupancy_cycles": field_record(
                    release,
                    "synthetic_trace",
                    evidence,
                    claimed=False,
                    identifiable=release is not None,
                ),
            },
            "synthetic_trace": {
                "template_id": item.template_id,
                "mode": item.mode,
                "configured_latency_cycles": latency,
                "configured_release_cycles": release,
                "configured_pipe": pipe_text,
                "measured_delta_cycles": measured_delta if measured_delta is not None else item.corrected_primary_delta,
                "marker_baseline_cycles": item.marker_baseline_cycles,
            },
        }

    latency_fit = fit_formula(latency_points)
    release_fit = fit_formula(release_points)
    latency_fit["evidence"] = formula_evidence
    release_fit["evidence"] = formula_evidence

    return {
        "schema_version": 1,
        "mode": "synthetic_calibration",
        "instruction": {
            "id": instruction_id,
            "asm": asm,
            "sew": 32,
            "llvm_sched_write": sched_write,
        },
        "measurements": measurements,
        "fit": {
            "latency_formula": latency_fit,
            "release_formula": release_fit,
        },
    }


def expected_value(config_instr: dict[str, Any], field: str, lmul: str) -> int | None:
    base = int_or_none(config_instr.get(f"{field}_base"))
    k = int_or_none(config_instr.get(f"{field}_lmul_k"))
    factor = LMUL_VALUE.get(lmul)
    if base is None or k is None or factor is None:
        return None
    return base + k * factor


def compare_profiles_to_config(
    profiles: dict[str, dict[str, Any]],
    timing_config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    instructions = timing_config.get("instructions")
    if not isinstance(instructions, dict):
        return rows, ["timing config has no instructions map"]

    for instr_id, raw_config in instructions.items():
        config_instr = raw_config if isinstance(raw_config, dict) else {}
        profile = profiles.get(instr_id)
        claimed_fields: list[str] = []
        issues: list[str] = []
        if profile is None:
            failures.append(f"{instr_id}: missing profile")
            rows.append(
                {
                    "instruction": instr_id,
                    "status": "missing_profile",
                    "claimed_fields": "none",
                    "notes": "missing profile.yaml",
                }
            )
            continue

        instr_meta = profile.get("instruction") if isinstance(profile.get("instruction"), dict) else {}
        asm = instr_meta.get("asm")
        if asm is not None:
            claimed_fields.append("asm")
            if asm != config_instr.get("asm"):
                issues.append(f"asm profile={asm} config={config_instr.get('asm')}")
        expected_pipe = config_instr.get("pipe")
        expected_resource = resource_for_pipe(str(expected_pipe)) if expected_pipe is not None else None
        measurements = profile.get("measurements") if isinstance(profile.get("measurements"), dict) else {}
        for lmul in LMUL_ORDER:
            lmul_measurement = measurements.get(lmul)
            if not isinstance(lmul_measurement, dict):
                issues.append(f"{lmul} missing measurement")
                continue
            llvm = lmul_measurement.get("llvm") if isinstance(lmul_measurement.get("llvm"), dict) else {}
            for profile_field, config_field in (("latency", "latency"), ("release_at_cycles", "release")):
                record = llvm.get(profile_field) if isinstance(llvm.get(profile_field), dict) else {}
                if not record.get("claimed"):
                    issues.append(f"{lmul}.{profile_field} not claimed")
                    continue
                value = int_or_none(record.get("value"))
                expected = expected_value(config_instr, config_field, lmul)
                claimed_fields.append(f"{lmul}.{profile_field}")
                if value != expected:
                    issues.append(f"{lmul}.{profile_field} profile={value} config={expected}")
            pipe_record = llvm.get("pipe_affinity") if isinstance(llvm.get("pipe_affinity"), dict) else {}
            if pipe_record.get("claimed"):
                claimed_fields.append(f"{lmul}.pipe_affinity")
                if pipe_record.get("value") != expected_pipe:
                    issues.append(f"{lmul}.pipe_affinity profile={pipe_record.get('value')} config={expected_pipe}")
            resource_record = llvm.get("resource_group") if isinstance(llvm.get("resource_group"), dict) else {}
            if resource_record.get("claimed"):
                claimed_fields.append(f"{lmul}.resource_group")
                if resource_record.get("value") != expected_resource:
                    issues.append(f"{lmul}.resource_group profile={resource_record.get('value')} config={expected_resource}")

        fit = profile.get("fit") if isinstance(profile.get("fit"), dict) else {}
        for fit_key, config_field in (("latency_formula", "latency"), ("release_formula", "release")):
            record = fit.get(fit_key) if isinstance(fit.get(fit_key), dict) else {}
            if not record.get("claimed"):
                issues.append(f"{fit_key} not claimed")
                continue
            claimed_fields.append(fit_key)
            base = int_or_none(record.get("base"))
            k = int_or_none(record.get("k"))
            expected_base = int_or_none(config_instr.get(f"{config_field}_base"))
            expected_k = int_or_none(config_instr.get(f"{config_field}_lmul_k"))
            if base != expected_base or k != expected_k:
                issues.append(f"{fit_key} profile={base}+{k}*LMUL config={expected_base}+{expected_k}*LMUL")

        status = "matched" if not issues else "mismatch"
        if issues:
            failures.extend(f"{instr_id}: {issue}" for issue in issues)
        rows.append(
            {
                "instruction": instr_id,
                "status": status,
                "claimed_fields": ", ".join(sorted(set(claimed_fields))) if claimed_fields else "none",
                "notes": "; ".join(issues) if issues else "all claimed synthetic fields match config",
            }
        )
    return rows, failures


def render_experiment_markdown(analysis: ExperimentAnalysis) -> str:
    lines = [
        "# Experiment Analysis",
        "",
        "Status: analyzed synthetic trace evidence.",
        "",
        f"- Trace: `{analysis.trace_path.as_posix()}`",
        f"- Experiment ID: `{analysis.experiment_id}`",
        f"- Template ID: `{analysis.template_id}`",
        f"- Mode: `{analysis.mode}`",
        f"- Instruction: `{analysis.instruction_id or 'unknown'}`",
        f"- LMUL: `{analysis.lmul or 'unknown'}`",
        f"- Marker baseline cycles: {analysis.marker_baseline_cycles}",
        f"- Marker count: {len(analysis.markers)}",
    ]
    primary = analysis.corrected_primary_delta
    lines.append(f"- Primary corrected delta: {'not available' if primary is None else str(primary) + ' cycles'}")

    if analysis.synthetic:
        lines.extend(["", "## Synthetic Metadata", ""])
        lines.append("| Field | Value |")
        lines.append("| --- | --- |")
        for key in ("timing_model", "pipe", "latency_cycles", "release_cycles", "measured_delta_cycles"):
            if key in analysis.synthetic:
                lines.append(f"| `{key}` | `{analysis.synthetic[key]}` |")

    lines.extend(["", "## Marker Deltas", ""])
    deltas = analysis.named_deltas or analysis.adjacent_deltas
    if deltas:
        lines.append("| From | To | Corrected delta cycles |")
        lines.append("| --- | --- | ---: |")
        for left, right, delta in deltas:
            lines.append(f"| `{left}` | `{right}` | {delta} |")
    else:
        lines.append("No usable marker deltas were found.")

    lines.extend(["", "## LLVM-Facing Claims", ""])
    if analysis.synthetic:
        lines.append(
            "For synthetic calibration, configured latency, release, and pipe "
            f"come from `{analysis.experiment_id}` at `{analysis.trace_path.as_posix()}`."
        )
    else:
        lines.append("No synthetic timing metadata is present, so no LLVM-facing timing field is claimed.")

    if analysis.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in analysis.warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def render_quality_report(analyses: list[ExperimentAnalysis], root: Path) -> str:
    synthetic_count = sum(1 for item in analyses if item.synthetic)
    covered = sorted({(item.instruction_id, item.lmul) for item in analyses if item.instruction_id and item.lmul})
    numeric_values = [item.corrected_primary_delta for item in analyses if item.corrected_primary_delta is not None]
    lines = [
        "# Experiment Quality Report",
        "",
        "Mode: real_platform_profile",
        "Gate status: NOT_READY",
        "Human approval status: absent",
        "",
        "This report is intentionally separate from synthetic golden matching. The current data set is synthetic dry-run evidence only, so the real-platform gate remains closed.",
        "",
        "## Coverage",
        "",
        f"Result root: `{root.as_posix()}`",
        f"Trace files analyzed: {len(analyses)}",
        f"Synthetic traces analyzed: {synthetic_count}",
        f"Instruction/LMUL pairs covered: {len(covered)}",
        "",
    ]
    if covered:
        lines.append("| Instruction | Covered LMULs |")
        lines.append("| --- | --- |")
        by_instr: dict[str, list[str]] = {}
        for instr, lmul in covered:
            if instr and lmul:
                by_instr.setdefault(instr, []).append(lmul)
        for instr in sorted(by_instr):
            lmuls = ", ".join(lmul for lmul in LMUL_ORDER if lmul in by_instr[instr])
            lines.append(f"| `{instr}` | `{lmuls}` |")
    else:
        lines.append("No real-platform trace coverage is available.")

    lines.extend(["", "## Stability", ""])
    if numeric_values:
        lines.append(f"Synthetic primary delta mean: {mean(numeric_values):.3f} cycles.")
    lines.append("No repeated real-platform measurements are available; stability is not established.")

    lines.extend(["", "## Confidence", ""])
    lines.append("Confidence for the real-platform profile is insufficient because current evidence is synthetic metadata, not hardware or gem5 timing output.")

    lines.extend(["", "## Assumptions", ""])
    lines.append("- Synthetic timestamp markers are treated as zero-cost observations after subtracting marker_baseline_cycles.")
    lines.append("- Processor issue width and real resource contention are not approved from this dry-run data.")
    lines.append("- Real platform mode must not use golden equality as an exit condition.")

    lines.extend(["", "## Human Approval", ""])
    lines.append("Human approval is absent. To pass, a future real-platform report must set an explicit approval status after coverage, stability, confidence, assumptions, and conflicts are reviewed.")
    return "\n".join(lines) + "\n"


def render_mismatch_report(rows: list[dict[str, Any]], failures: list[str]) -> str:
    status = "PASS" if not failures else "FAIL"
    mismatch_text = "none" if not failures else str(len(failures))
    lines = [
        "# Synthetic Calibration Mismatch Report",
        "",
        "Mode: synthetic_calibration",
        f"Gate status: {status}",
        f"Claimed mismatches: {mismatch_text}",
        "",
        "Synthetic calibration compares only fields claimed by generated profiles against `config/rvv_timing_model.yaml`. Unknown or not-identifiable fields are explicit in the profiles and are not used as golden-equality claims.",
        "",
        "## Instruction Status",
        "",
        "| Instruction | Synthetic comparison status | Claimed fields | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['instruction']}` | {row['status']} | {row['claimed_fields']} | {row['notes']} |"
        )
    if failures:
        lines.extend(["", "## Claimed Field Mismatches", ""])
        for failure in failures:
            lines.append(f"- {failure}")
    else:
        lines.extend(["", "## Claimed Field Mismatches", "", "None."])

    lines.extend(["", "## Experiment Design Limits", ""])
    lines.append("- `NumMicroOps`, `SingleIssue`, `ReadAdvance`, and separate writeback stage fields are recorded but unclaimed by the current synthetic traces.")
    lines.append("- Synthetic traces validate analyzer plumbing and configured values; they are not real-platform measurements.")
    lines.append("- Future real-platform gates must use coverage, stability, confidence, assumptions, conflict resolution, and human approval instead of golden equality.")
    return "\n".join(lines) + "\n"


def render_profile_yaml(profile: dict[str, Any]) -> str:
    return render_yaml(profile) + "\n"


def find_traces(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("**/experiments/**/trace.json"), key=lambda path: path.as_posix())


def load_timing_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return parse_yamlish(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze RVV marker trace JSON files.")
    parser.add_argument("--all", action="store_true", help="Accepted for the plan's one-command flow.")
    parser.add_argument("--root", default="results", help="Result root to scan.")
    parser.add_argument("--config", default="config/rvv_timing_model.yaml", help="Synthetic timing config.")
    parser.add_argument(
        "--aggregate",
        default="results/common/experiment_quality.md",
        help="Real-platform quality report path.",
    )
    parser.add_argument(
        "--mismatch-report",
        default="results/common/mismatch_report.md",
        help="Synthetic calibration mismatch report path.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without changing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    trace_paths = find_traces(root)
    analyses = [analyze_trace(path) for path in trace_paths]
    timing_config = load_timing_config(Path(args.config))
    config_instructions = timing_config.get("instructions") if isinstance(timing_config.get("instructions"), dict) else {}

    by_instruction: dict[str, list[ExperimentAnalysis]] = {}
    for item in analyses:
        if item.instruction_id:
            by_instruction.setdefault(item.instruction_id, []).append(item)

    instruction_order = list(config_instructions) if isinstance(config_instructions, dict) else sorted(by_instruction)
    profiles: dict[str, dict[str, Any]] = {}
    for instruction_id in instruction_order:
        config_instr = config_instructions.get(instruction_id) if isinstance(config_instructions, dict) else None
        profiles[instruction_id] = build_profile(instruction_id, by_instruction.get(instruction_id, []), config_instr)

    rows, failures = compare_profiles_to_config(profiles, timing_config)

    writes: list[tuple[Path, str]] = []
    for item in analyses:
        writes.append((item.trace_path.parent / "analysis.md", render_experiment_markdown(item)))
    for instruction_id, profile in profiles.items():
        writes.append((root / instruction_id / "profile.yaml", render_profile_yaml(profile)))
    writes.append((Path(args.aggregate), render_quality_report(analyses, root)))
    writes.append((Path(args.mismatch_report), render_mismatch_report(rows, failures)))

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
