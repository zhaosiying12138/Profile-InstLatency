#!/usr/bin/env python3
"""Analyze RVV profiling traces and synthesize LLVM-facing profiles.

The analyzer is stdlib-only and intentionally conservative.  Claimed LLVM
timing fields come from raw marker deltas plus experiment metadata.  Synthetic
dry-run traces may carry configured timing metadata, but that metadata is used
only as reference material for calibration mismatch reports and trace notes.
Fields without enough non-circular marker evidence are left explicit and
unclaimed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
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
PIPE0_CLUSTER_ANCHORS = {"vcpop_m", "viota_m", "vslideup_vx"}
PIPE1_CLUSTER_ANCHORS = {"vdivu_vv", "vrgather_vv", "vredsum_vs"}
NON_REQUIRED_REAL_TEMPLATES = {"T00_BASELINE_MARKER"}
REQUIRED_REAL_LLVM_FIELDS = ("Latency", "ReleaseAtCycles", "ProcResource", "NumMicroOps", "SingleIssue")
FIELD_STATUS_FILENAME = "real_platform_field_status.json"
BLOCKING_FIELD_STATUSES = {
    "conflict",
    "insufficient_evidence",
    "missing",
    "unknown",
    "invalid",
    "error",
    "not_set",
}
APPROVAL_FILENAMES = {
    "approval.json",
    "human_approval.json",
    "experiment_approval.json",
    "real_platform_approval.json",
    "approval.md",
    "human_approval.md",
    "experiment_approval.md",
    "real_platform_approval.md",
}
QUALITY_ASSUMPTIONS = (
    "Real-platform approval is based on gem5 traces classified by trace JSON mode/backend fields, not by result path.",
    "Synthetic calibration traces remain reference-only for mismatch reporting and are not counted as real-platform coverage.",
    "Required real templates are inferred from non-baseline synthetic template inventory because that inventory defines the current latency/resource suite.",
    "Repeated measurements mean at least two real gem5 traces for the same template/instruction/LMUL/body signature with identical corrected primary deltas.",
    "Timestamp markers use the documented label-PC wrapper: marker labels emit no instructions, adjacent marker labels may share one PC, and the checked-in real T00 baseline must show zero corrected marker delta.",
)
RUN_RESULT_DIR_RE = re.compile(r"r\d+$", re.IGNORECASE)


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
    backend: str
    mode: str
    dry_run_trace: bool
    marker_baseline_cycles: int
    instruction_id: str | None
    asm: str | None
    llvm_sched_write: str | None
    lmul: str | None
    body: dict[str, Any]
    pair_instruction_id: str | None
    scaling_shape: str | None
    timestamp_model_kind: str | None
    timestamp_model_occupies_issue_slot: bool | None
    marker_definitions: tuple[dict[str, Any], ...]
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


def bool_or_false(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


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
    return first_value(
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
    trace_warnings = trace_doc.get("warnings")
    if isinstance(trace_warnings, list):
        warnings.extend(str(warning) for warning in trace_warnings if str(warning).strip())
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
    body_doc = experiment_doc.get("body") if isinstance(experiment_doc.get("body"), dict) else {}
    pair_doc = experiment_doc.get("pair_instruction") if isinstance(experiment_doc.get("pair_instruction"), dict) else {}
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
    backend = str(first_value(trace_doc.get("backend"), trace_metadata(trace_doc).get("backend"), "unknown"))
    dry_run_trace = bool_or_false(trace_doc.get("dry_run_trace"))
    timestamp_model = trace_doc.get("timestamp_model")
    if not isinstance(timestamp_model, dict):
        timestamp_model = {}
    marker_definitions = trace_doc.get("markers")
    if not isinstance(marker_definitions, list):
        marker_definitions = []

    return ExperimentAnalysis(
        trace_path=trace_path,
        experiment_path=experiment_path if experiment_path.exists() else None,
        experiment_id=experiment_id,
        template_id=template_id,
        backend=backend,
        mode=mode,
        dry_run_trace=dry_run_trace,
        marker_baseline_cycles=baseline,
        instruction_id=str(instruction_id) if instruction_id is not None else None,
        asm=str(asm) if asm is not None else None,
        llvm_sched_write=str(llvm_sched_write) if llvm_sched_write is not None else None,
        lmul=str(lmul) if lmul is not None else None,
        body=dict(body_doc),
        pair_instruction_id=str(pair_doc["id"]) if pair_doc.get("id") is not None else None,
        scaling_shape=str(body_doc["scaling_shape"]) if body_doc.get("scaling_shape") is not None else None,
        timestamp_model_kind=str(timestamp_model["kind"]) if timestamp_model.get("kind") is not None else None,
        timestamp_model_occupies_issue_slot=bool_or_false(timestamp_model.get("occupies_issue_slot"))
        if "occupies_issue_slot" in timestamp_model
        else None,
        marker_definitions=tuple(dict(item) for item in marker_definitions if isinstance(item, dict)),
        synthetic=dict(synthetic),
        markers=markers,
        adjacent_deltas=tuple(adjacent),
        named_deltas=tuple(named),
        warnings=tuple(warnings),
    )


def evidence_for(item: ExperimentAnalysis) -> list[str]:
    return [f"{item.experiment_id} @ {item.trace_path.as_posix()}"]


def raw_marker_evidence(item: ExperimentAnalysis, detail: str) -> str:
    return f"raw_marker_delta:{item.experiment_id}:{detail} @ {item.trace_path.as_posix()}"


def body_int(item: ExperimentAnalysis, *keys: str) -> int | None:
    for key in keys:
        value = item.body.get(key)
        result = int_or_none(value)
        if result is not None:
            return result
    return None


def effective_shape(item: ExperimentAnalysis) -> str:
    if item.template_id == "T30_LMUL_SCALING" and item.scaling_shape:
        return item.scaling_shape
    return item.template_id


def same_value(values: list[int]) -> int | None:
    if not values:
        return None
    first = values[0]
    if all(value == first for value in values):
        return first
    return None


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
    source: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "value": value,
        "confidence": confidence,
        "claimed": claimed,
        "identifiable": identifiable,
        "evidence": evidence,
    }
    if source:
        record["source"] = source
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


def infer_release_record(items: list[ExperimentAnalysis]) -> dict[str, Any]:
    observations: list[tuple[int, int, str]] = []
    skipped: list[str] = []
    for item in items:
        if effective_shape(item) != "T10_INDEPENDENT_STREAM_THROUGHPUT":
            continue
        iterations = body_int(item, "iterations", "stream_length", "sample_count")
        delta = item.corrected_primary_delta
        if iterations is None or iterations <= 0 or delta is None:
            skipped.append(raw_marker_evidence(item, "throughput_missing_delta_or_iterations"))
            continue
        if delta % iterations != 0:
            skipped.append(raw_marker_evidence(item, f"throughput_non_integer:delta={delta}:iterations={iterations}"))
            continue
        value = delta // iterations
        observations.append(
            (
                iterations,
                value,
                raw_marker_evidence(
                    item,
                    f"{effective_shape(item)}:delta={delta}:iterations={iterations}:release={value}",
                ),
            )
        )

    evidence = [entry for _iterations, _value, entry in observations] + skipped
    if not observations:
        return field_record(
            None,
            "insufficient_raw_marker_evidence",
            evidence,
            claimed=False,
            identifiable=False,
            reason="No T10/T30 throughput marker delta with an exact integer delta/iterations ratio is available.",
        )
    distinct_lengths = {iterations for iterations, _value, _entry in observations}
    if len(distinct_lengths) < 2:
        return field_record(
            None,
            "insufficient_raw_marker_evidence",
            evidence,
            claimed=False,
            identifiable=False,
            reason="Throughput release requires at least two stream lengths for the same instruction/LMUL.",
        )
    value = same_value([value for _iterations, value, _entry in observations])
    if value is None:
        return field_record(
            None,
            "conflict_raw_marker_evidence",
            evidence,
            claimed=False,
            identifiable=False,
            reason="T10/T30 throughput marker deltas imply conflicting release values.",
        )
    return field_record(
        value,
        "raw_marker_inference",
        evidence,
        claimed=True,
        source="raw_marker_observation",
    )


def infer_latency_record(items: list[ExperimentAnalysis]) -> dict[str, Any]:
    chain_observations: list[tuple[int, str]] = []
    chain_skipped: list[str] = []
    sweep_by_k: dict[int, list[tuple[int, str]]] = {}
    sweep_skipped: list[str] = []

    for item in items:
        shape = effective_shape(item)
        delta = item.corrected_primary_delta
        if shape == "T11_SELF_RAW_CHAIN":
            iterations = body_int(item, "iterations", "chain_length", "sample_count")
            if iterations is None or iterations <= 0 or delta is None:
                chain_skipped.append(raw_marker_evidence(item, "raw_chain_missing_delta_or_iterations"))
                continue
            if delta % iterations != 0:
                chain_skipped.append(raw_marker_evidence(item, f"raw_chain_non_integer:delta={delta}:iterations={iterations}"))
                continue
            value = delta // iterations
            chain_observations.append(
                (
                    value,
                    raw_marker_evidence(
                        item,
                        f"{shape}:delta={delta}:iterations={iterations}:latency={value}",
                    ),
                )
            )
        elif shape == "T12_CONSUMER_RAW_GAP":
            filler_count = body_int(item, "filler_count")
            if filler_count is None or delta is None:
                sweep_skipped.append(raw_marker_evidence(item, "raw_gap_missing_delta_or_filler_count"))
                continue
            value = delta - filler_count
            if value < 0:
                sweep_skipped.append(raw_marker_evidence(item, f"raw_gap_negative_readiness:delta={delta}:filler={filler_count}"))
                continue
            sweep_by_k.setdefault(filler_count, []).append(
                (
                    value,
                    raw_marker_evidence(
                        item,
                        f"{shape}:delta={delta}:filler_count={filler_count}:readiness={value}",
                    ),
                )
            )

    evidence = [entry for _value, entry in chain_observations]
    evidence.extend(entry for values in sweep_by_k.values() for _value, entry in values)
    evidence.extend(chain_skipped)
    evidence.extend(sweep_skipped)

    inferred: list[int] = []
    if chain_observations:
        chain_value = same_value([value for value, _entry in chain_observations])
        if chain_value is None:
            return field_record(
                None,
                "conflict_raw_marker_evidence",
                evidence,
                claimed=False,
                identifiable=False,
                reason="T11 RAW chain marker deltas imply conflicting latency values.",
            )
        inferred.append(chain_value)

    if sweep_by_k:
        if len(sweep_by_k) < 2:
            evidence.extend(entry for values in sweep_by_k.values() for _value, entry in values)
        else:
            sweep_values = [value for values in sweep_by_k.values() for value, _entry in values]
            sweep_value = same_value(sweep_values)
            if sweep_value is None:
                return field_record(
                    None,
                    "conflict_raw_marker_evidence",
                    evidence,
                    claimed=False,
                    identifiable=False,
                    reason="T12 gap sweep marker deltas do not imply a single readiness value.",
                )
            inferred.append(sweep_value)

    if not inferred:
        reason = "No exact T11 RAW-chain latency or multi-K T12 readiness sweep is available."
        if sweep_by_k and len(sweep_by_k) < 2:
            reason = "T12 readiness requires at least two filler-count values for the same instruction/LMUL."
        return field_record(
            None,
            "insufficient_raw_marker_evidence",
            evidence,
            claimed=False,
            identifiable=False,
            reason=reason,
        )

    value = same_value(inferred)
    if value is None:
        return field_record(
            None,
            "conflict_raw_marker_evidence",
            evidence,
            claimed=False,
            identifiable=False,
            reason="T11 RAW-chain and T12 readiness observations disagree.",
        )
    return field_record(
        value,
        "raw_marker_inference",
        evidence,
        claimed=True,
        source="raw_marker_observation",
    )


def release_value_for(
    by_instruction: dict[str, list[ExperimentAnalysis]],
    instruction_id: str,
    lmul: str,
) -> int | None:
    record = infer_release_record([item for item in by_instruction.get(instruction_id, []) if item.lmul == lmul])
    return int_or_none(record.get("value")) if record.get("claimed") else None


def infer_resource_records(
    instruction_id: str,
    lmul: str,
    items: list[ExperimentAnalysis],
    by_instruction: dict[str, list[ExperimentAnalysis]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    release_a = release_value_for(by_instruction, instruction_id, lmul)
    pair_evidence: list[str] = []
    overlap_partners: set[str] = set()
    serial_partners: set[str] = set()

    for item in items:
        if effective_shape(item) != "T20_PAIRWISE_PIPE_CLASSIFICATION":
            continue
        if item.instruction_id == instruction_id:
            other = item.pair_instruction_id
            side = "A"
        elif item.pair_instruction_id == instruction_id:
            other = item.instruction_id
            side = "B"
        else:
            continue
        iterations = body_int(item, "iterations", "pair_count")
        delta = item.corrected_primary_delta
        if other is None or iterations is None or iterations <= 0 or delta is None:
            pair_evidence.append(raw_marker_evidence(item, "pairwise_missing_delta_partner_or_iterations"))
            continue
        if delta % iterations != 0:
            pair_evidence.append(raw_marker_evidence(item, f"pairwise_non_integer:delta={delta}:iterations={iterations}:other={other}"))
            continue
        release_b = release_value_for(by_instruction, other, lmul)
        pair_cycles = delta // iterations
        detail = f"T20_PAIRWISE_PIPE_CLASSIFICATION:other={other}:delta={delta}:iterations={iterations}:cycles_per_pair={pair_cycles}"
        if release_a is None or release_b is None:
            pair_evidence.append(raw_marker_evidence(item, f"{detail}:single_release_missing"))
            continue
        pair_evidence.append(
            raw_marker_evidence(
                item,
                f"{detail}:subject_side={side}:single_release_subject={release_a}:single_release_other={release_b}",
            )
        )
        if pair_cycles <= max(release_a, release_b) and pair_cycles < release_a + release_b:
            overlap_partners.add(other)
        elif pair_cycles >= release_a + release_b:
            serial_partners.add(other)

    if serial_partners:
        cluster_ids = {instruction_id, *serial_partners}
        pipe: str | None
        if cluster_ids & PIPE0_CLUSTER_ANCHORS:
            pipe = "pipe0"
        elif cluster_ids & PIPE1_CLUSTER_ANCHORS:
            pipe = "pipe1"
        else:
            pipe = None
        if pipe is not None:
            reason = (
                "T20 pair timing has same-resource serialization edges; the pipe label is "
                "assigned by the experiment schedule-family anchor for that serialization cluster."
            )
            pipe_record = field_record(
                pipe,
                "raw_marker_pairwise_inference",
                pair_evidence,
                claimed=True,
                source="raw_marker_observation",
                reason=reason,
            )
            resource_record = field_record(
                resource_for_pipe(pipe),
                "raw_marker_pairwise_inference",
                pair_evidence,
                claimed=True,
                source="raw_marker_observation",
                reason=reason,
            )
            proc_record = field_record(
                resource_for_pipe(pipe),
                "raw_marker_pairwise_inference",
                pair_evidence,
                claimed=True,
                source="raw_marker_observation",
                reason=reason,
            )
            return proc_record, resource_record, pipe_record, pair_evidence

    if not serial_partners and len(overlap_partners) >= 2:
        pipe_record = field_record(
            "any",
            "raw_marker_pairwise_inference",
            pair_evidence,
            claimed=True,
            source="raw_marker_observation",
            reason="T20 pair timing overlaps with multiple partners relative to single-instruction throughput.",
        )
        resource_record = field_record(
            resource_for_pipe("any"),
            "raw_marker_pairwise_inference",
            pair_evidence,
            claimed=True,
            source="raw_marker_observation",
            reason="T20 pair timing supports a flexible vector pipe resource group.",
        )
        proc_record = field_record(
            resource_for_pipe("any"),
            "raw_marker_pairwise_inference",
            pair_evidence,
            claimed=True,
            source="raw_marker_observation",
            reason="T20 pair timing supports a flexible vector pipe resource group.",
        )
        return proc_record, resource_record, pipe_record, pair_evidence

    reason = "T20 pair timing is insufficient to map this instruction to a pipe or resource group."
    if serial_partners and not overlap_partners:
        reason = "T20 pair timing indicates serialization but does not identify pipe0 versus pipe1."
    pipe_record = field_record(
        None,
        "insufficient_raw_marker_evidence",
        pair_evidence,
        claimed=False,
        identifiable=False,
        reason=reason,
    )
    resource_record = field_record(
        None,
        "insufficient_raw_marker_evidence",
        pair_evidence,
        claimed=False,
        identifiable=False,
        reason=reason,
    )
    proc_record = field_record(
        None,
        "insufficient_raw_marker_evidence",
        pair_evidence,
        claimed=False,
        identifiable=False,
        reason=reason,
    )
    return proc_record, resource_record, pipe_record, pair_evidence


def build_profile(
    instruction_id: str,
    analyses: list[ExperimentAnalysis],
    config_instr: dict[str, Any] | None,
    by_instruction: dict[str, list[ExperimentAnalysis]],
) -> dict[str, Any]:
    by_lmul: dict[str, list[ExperimentAnalysis]] = {
        lmul: [item for item in analyses if item.lmul == lmul] for lmul in LMUL_ORDER
    }
    first = next((item for item in analyses if item.instruction_id == instruction_id and item.lmul in LMUL_ORDER), None)
    asm = first.asm if first and first.asm else (config_instr or {}).get("asm")
    sched_write = first.llvm_sched_write if first and first.llvm_sched_write else None

    measurements: dict[str, Any] = {}
    latency_points: dict[str, int] = {}
    release_points: dict[str, int] = {}
    latency_formula_evidence: list[str] = []
    release_formula_evidence: list[str] = []

    for lmul in LMUL_ORDER:
        lmul_items = by_lmul.get(lmul, [])
        if not lmul_items:
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

        latency_record = infer_latency_record(lmul_items)
        release_record = infer_release_record(lmul_items)
        proc_record, resource_record, pipe_record, pair_evidence = infer_resource_records(
            instruction_id,
            lmul,
            lmul_items,
            by_instruction,
        )
        latency = int_or_none(latency_record.get("value")) if latency_record.get("claimed") else None
        release = int_or_none(release_record.get("value")) if release_record.get("claimed") else None
        if latency is not None:
            latency_points[lmul] = latency
            latency_formula_evidence.extend(str(entry) for entry in latency_record.get("evidence", []))
        if release is not None:
            release_points[lmul] = release
            release_formula_evidence.extend(str(entry) for entry in release_record.get("evidence", []))

        synthetic_references: list[str] = []
        for item in lmul_items:
            if not item.synthetic:
                continue
            synthetic_references.append(
                "experiment="
                f"{item.experiment_id};template={item.template_id};"
                f"configured_latency={int_or_none(item.synthetic.get('latency_cycles'))};"
                f"configured_release={int_or_none(item.synthetic.get('release_cycles'))};"
                f"configured_pipe={item.synthetic.get('pipe')};"
                f"synthetic_delta={int_or_none(item.synthetic.get('measured_delta_cycles'))}"
            )

        measurements[lmul] = {
            "llvm": {
                "proc_resource": proc_record,
                "resource_group": resource_record,
                "pipe_affinity": pipe_record,
                "latency": latency_record,
                "release_at_cycles": release_record,
                "acquire_at_cycles": field_record([], "assumed_default", [], claimed=False),
                "num_micro_ops": field_record(
                    None,
                    "not_identifiable",
                    pair_evidence,
                    claimed=False,
                    identifiable=False,
                    reason="T20/T21 marker evidence is not sufficient to decompose scheduler writes into micro-ops.",
                ),
                "single_issue": field_record(
                    None,
                    "not_identifiable",
                    pair_evidence,
                    claimed=False,
                    identifiable=False,
                    reason="Scalar-pairing evidence is not sufficient to claim SingleIssue.",
                ),
                "read_advance": field_record(
                    None,
                    "not_identifiable",
                    latency_record.get("evidence", []),
                    claimed=False,
                    identifiable=False,
                    reason="Consumer-specific bypass evidence is outside the current claimed marker inference.",
                ),
            },
            "hardware_interpretation": {
                "issue_delay_cycles": field_record(
                    None,
                    "not_identifiable",
                    latency_record.get("evidence", []),
                    claimed=False,
                    identifiable=False,
                    reason="Current marker traces do not split issue delay from execution latency.",
                ),
                "execute_latency_cycles": field_record(
                    latency,
                    latency_record.get("confidence", "insufficient_raw_marker_evidence"),
                    latency_record.get("evidence", []),
                    claimed=False,
                    identifiable=latency is not None,
                    source=latency_record.get("source") if isinstance(latency_record.get("source"), str) else None,
                ),
                "writeback_latency_cycles": field_record(
                    None,
                    "not_identifiable",
                    latency_record.get("evidence", []),
                    claimed=False,
                    identifiable=False,
                    reason="LLVM/gem5 marker experiments observe producer-consumer readiness, not a separate physical writeback stage.",
                ),
                "resource_occupancy_cycles": field_record(
                    release,
                    release_record.get("confidence", "insufficient_raw_marker_evidence"),
                    release_record.get("evidence", []),
                    claimed=False,
                    identifiable=release is not None,
                    source=release_record.get("source") if isinstance(release_record.get("source"), str) else None,
                ),
            },
            "raw_observations": {
                "latency": latency_record,
                "release": release_record,
                "pairing_evidence": pair_evidence,
            },
            "synthetic_reference": {
                "source": "trace.synthetic_reference_only",
                "used_for_claims": False,
                "entries": synthetic_references,
            },
        }

    latency_fit = fit_formula(latency_points)
    release_fit = fit_formula(release_points)
    latency_fit["evidence"] = latency_formula_evidence
    release_fit["evidence"] = release_formula_evidence
    if latency_fit.get("claimed"):
        latency_fit["source"] = "raw_marker_observation"
        latency_fit["confidence"] = "raw_marker_formula_fit"
    else:
        latency_fit["confidence"] = "insufficient_raw_marker_evidence"
    if release_fit.get("claimed"):
        release_fit["source"] = "raw_marker_observation"
        release_fit["confidence"] = "raw_marker_formula_fit"
    else:
        release_fit["confidence"] = "insufficient_raw_marker_evidence"

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
                "notes": "; ".join(issues) if issues else "all claimed raw-inferred fields match config",
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
        lines.extend(["", "## Synthetic Reference Metadata", ""])
        lines.append("Synthetic values are reference-only and are not used as LLVM-facing claims.")
        lines.append("")
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
    lines.append(
        "LLVM-facing timing fields are claimable only through raw marker-delta inference "
        "across the relevant template family. Synthetic metadata is reference-only."
    )

    if analysis.warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in analysis.warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines) + "\n"


def normalized_id(value: Any) -> str:
    if value is None or value == "":
        return "unknown"
    return str(value)


def trace_classification(item: ExperimentAnalysis) -> str:
    mode = item.mode.lower()
    backend = item.backend.lower()
    synthetic_signal = "synthetic" in mode or "synthetic" in backend
    real_signal = "real_platform" in mode or mode == "real" or mode.startswith("real_") or "gem5" in backend
    if synthetic_signal and real_signal:
        return "conflict"
    if synthetic_signal:
        return "synthetic"
    if real_signal:
        return "real"
    return "unknown"


def is_real_gem5(item: ExperimentAnalysis) -> bool:
    return trace_classification(item) == "real" and "gem5" in item.backend.lower()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def common_result_root(root: Path) -> Path:
    if root.name == "common":
        return root
    candidate = root / "common"
    if candidate.exists():
        return candidate
    return root


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_key(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def get_first_by_keys(data: dict[str, Any], names: set[str]) -> Any:
    for key, value in data.items():
        if canonical_json_key(key) in names:
            return value
    return None


def walk_json_dicts(data: Any, path: tuple[str, ...] = ("$",)) -> list[tuple[tuple[str, ...], dict[str, Any]]]:
    found: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    if isinstance(data, dict):
        found.append((path, data))
        for key, value in data.items():
            found.extend(walk_json_dicts(value, path + (str(key),)))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            found.extend(walk_json_dicts(value, path + (f"[{index}]",)))
    return found


def json_path_text(path: tuple[str, ...]) -> str:
    text = ""
    for part in path:
        if not text:
            text = part
        elif part.startswith("["):
            text += part
        else:
            text += f".{part}"
    return text


def path_value_after(path: tuple[str, ...], marker: str) -> str | None:
    for index, part in enumerate(path[:-1]):
        if canonical_json_key(part) != marker:
            continue
        candidate = path[index + 1]
        if not candidate.startswith("["):
            return candidate
    return None


def normalize_required_field(value: Any) -> str | None:
    if value is None:
        return None
    token = re.sub(r"[^a-z0-9]", "", str(value).lower())
    lookup = {
        re.sub(r"[^a-z0-9]", "", field.lower()): field
        for field in REQUIRED_REAL_LLVM_FIELDS
    }
    lookup.update(
        {
            "latency": "Latency",
            "releaseatcycles": "ReleaseAtCycles",
            "release": "ReleaseAtCycles",
            "procresource": "ProcResource",
            "resource": "ProcResource",
            "nummicroops": "NumMicroOps",
            "microops": "NumMicroOps",
            "singleissue": "SingleIssue",
        }
    )
    return lookup.get(token)


def normalize_field_status(value: Any) -> str:
    if value is None:
        return "missing"
    text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if not text:
        return "missing"
    if "conflict" in text:
        return "conflict"
    if text.startswith("insufficient") or "insufficient_evidence" in text or "not_enough" in text:
        return "insufficient_evidence"
    if "unknown" in text:
        return "unknown"
    return text


def is_blocking_field_status(status: str) -> bool:
    return normalize_field_status(status) in BLOCKING_FIELD_STATUSES


def field_status_risk_id(instruction_id: Any, lmul: Any, field: Any, status: Any) -> str:
    return (
        "llvm_field_status:"
        f"{normalized_id(instruction_id)}:"
        f"{normalized_id(lmul)}:"
        f"{normalize_required_field(field) or normalized_id(field)}:"
        f"{normalize_field_status(status)}"
    )


def extract_field_status_records(data: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for path, item in walk_json_dicts(data):
        path_text = json_path_text(path)
        field = normalize_required_field(
            first_value(
                get_first_by_keys(item, {"field", "llvm_field", "field_name", "name"}),
                path[-1] if path else None,
            )
        )
        if field is None:
            continue
        raw_status = first_value(
            get_first_by_keys(item, {"status", "state", "confidence", "resolution"}),
            "missing",
        )
        status = normalize_field_status(raw_status)
        instruction_id = first_value(
            get_first_by_keys(item, {"instruction_id", "instruction", "instr", "instr_id"}),
            path_value_after(path, "instructions"),
            path_value_after(path, "instruction"),
            "unknown",
        )
        lmul = first_value(
            get_first_by_keys(item, {"lmul", "vector_lmul"}),
            path_value_after(path, "lmuls"),
            path_value_after(path, "lmul"),
            "unknown",
        )
        key = (path_text, normalized_id(instruction_id), normalized_id(lmul), field, status)
        if key in seen:
            continue
        seen.add(key)
        record = {
            "risk_id": field_status_risk_id(instruction_id, lmul, field, status),
            "instruction_id": normalized_id(instruction_id),
            "lmul": normalized_id(lmul),
            "field": field,
            "status": status,
            "source_status": raw_status,
            "json_path": path_text,
        }
        reason = get_first_by_keys(item, {"reason", "diagnostic", "message", "summary"})
        if reason is not None:
            record["reason"] = str(reason)
        evidence = get_first_by_keys(item, {"evidence", "evidence_paths", "traces", "trace_paths"})
        if evidence is not None:
            record["evidence"] = evidence
        records.append(record)
    return records


def missing_required_field_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = sorted(
        {
            (record["instruction_id"], record["lmul"])
            for record in records
            if record.get("instruction_id") not in (None, "unknown") and record.get("lmul") not in (None, "unknown")
        }
    )
    present = {
        (record.get("instruction_id"), record.get("lmul"), record.get("field"))
        for record in records
    }
    missing: list[dict[str, Any]] = []
    for instruction_id, lmul in pairs:
        for field in REQUIRED_REAL_LLVM_FIELDS:
            if (instruction_id, lmul, field) in present:
                continue
            missing.append(
                {
                    "risk_id": field_status_risk_id(instruction_id, lmul, field, "missing"),
                    "instruction_id": instruction_id,
                    "lmul": lmul,
                    "field": field,
                    "status": "missing",
                    "source_status": "missing",
                    "json_path": "$",
                    "reason": "Required LLVM-facing field has no status record.",
                }
            )
    return missing


def load_real_platform_field_status(root: Path) -> dict[str, Any]:
    path = common_result_root(root) / FIELD_STATUS_FILENAME
    summary: dict[str, Any] = {
        "path": path.as_posix(),
        "exists": path.exists(),
        "sha256": None,
        "required_fields": list(REQUIRED_REAL_LLVM_FIELDS),
        "records_total": 0,
        "status_counts": {},
        "unresolved_total": 0,
        "unresolved": [],
        "missing_required_total": 0,
        "missing_required": [],
        "status": "missing",
    }
    if not path.exists():
        summary["unresolved"] = [
            {
                "risk_id": "real_platform_field_status:missing",
                "status": "missing",
                "field": "all",
                "reason": f"Missing {FIELD_STATUS_FILENAME}; cannot verify required LLVM-facing field status.",
            }
        ]
        summary["unresolved_total"] = 1
        return summary

    summary["sha256"] = sha256_file(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        summary.update(
            {
                "status": "invalid",
                "error": str(error),
                "unresolved_total": 1,
                "unresolved": [
                    {
                        "risk_id": "real_platform_field_status:invalid_json",
                        "status": "invalid",
                        "field": "all",
                        "reason": f"{FIELD_STATUS_FILENAME} is not valid JSON: {error}",
                    }
                ],
            }
        )
        return summary

    records = extract_field_status_records(data)
    missing = missing_required_field_records(records)
    unresolved = [record for record in records if is_blocking_field_status(record["status"])] + missing
    status_counts = Counter(record["status"] for record in records)
    summary.update(
        {
            "status": "ready" if records and not unresolved else "blocked",
            "records_total": len(records),
            "status_counts": sorted_counter(status_counts),
            "unresolved_total": len(unresolved),
            "unresolved": unresolved,
            "missing_required_total": len(missing),
            "missing_required": missing,
        }
    )
    if not records:
        summary.update(
            {
                "status": "no_records",
                "unresolved_total": 1,
                "unresolved": [
                    {
                        "risk_id": "real_platform_field_status:no_records",
                        "status": "insufficient_evidence",
                        "field": "all",
                        "reason": f"{FIELD_STATUS_FILENAME} contains no required LLVM-facing field status records.",
                    }
                ],
            }
        )
    return summary


def values_from_json_key(data: Any, names: set[str]) -> list[Any]:
    values: list[Any] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if canonical_json_key(key) in names:
                values.append(value)
            values.extend(values_from_json_key(value, names))
    elif isinstance(data, list):
        for value in data:
            values.extend(values_from_json_key(value, names))
    return values


def risk_ids_from_value(value: Any) -> set[str]:
    risk_ids: set[str] = set()
    if isinstance(value, str):
        if value.strip():
            risk_ids.add(value.strip())
    elif isinstance(value, list):
        for item in value:
            risk_ids.update(risk_ids_from_value(item))
    elif isinstance(value, dict):
        risk_id = get_first_by_keys(value, {"risk_id", "id"})
        if risk_id is not None and str(risk_id).strip():
            risk_ids.add(str(risk_id).strip())
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                risk_ids.update(risk_ids_from_value(nested))
    return risk_ids


def accepted_risk_ids_from_document(data: dict[str, Any]) -> set[str]:
    accepted: set[str] = set()
    for value in values_from_json_key(
        data,
        {
            "accepted_risk_ids",
            "accepted_risks",
            "accepted_unresolved_risks",
            "accepted_field_status_risks",
            "field_status_accepted_risks",
            "risk_acceptance",
            "risk_acceptances",
        },
    ):
        accepted.update(risk_ids_from_value(value))
    return accepted


def field_status_risks_accepted(field_status: dict[str, Any], approval: dict[str, Any]) -> bool:
    unresolved = field_status.get("unresolved")
    if not isinstance(unresolved, list) or not unresolved:
        return True
    accepted = set(str(value) for value in approval.get("accepted_risk_ids", []) if str(value).strip())
    if "*" in accepted or "all" in {value.lower() for value in accepted}:
        return True
    required = {
        str(item.get("risk_id"))
        for item in unresolved
        if isinstance(item, dict) and item.get("risk_id")
    }
    return bool(required) and required <= accepted


def marker_definition_status(item: ExperimentAnalysis) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not item.marker_definitions:
        failures.append("trace has no marker metadata definitions")
        return False, failures
    for marker in item.marker_definitions:
        label = marker.get("label", marker.get("name", "unknown"))
        if marker.get("zero_cost") is not True:
            failures.append(f"marker {label} is not declared zero_cost: true")
        if marker.get("occupies_issue_slot") is not False:
            failures.append(f"marker {label} is not declared occupies_issue_slot: false")
    return not failures, failures


def build_marker_contract(real_gem5_items: list[ExperimentAnalysis]) -> dict[str, Any]:
    candidates = [
        item
        for item in real_gem5_items
        if item.template_id == "T00_BASELINE_MARKER" and item.experiment_id == "t00-marker"
    ]
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for item in sorted(candidates, key=lambda entry: entry.trace_path.as_posix()):
        named_delta = next(
            (delta for left, right, delta in item.named_deltas if left == "t0" and right == "t1"),
            item.corrected_primary_delta,
        )
        marker_pcs = {
            marker.name: marker.pc
            for marker in item.markers
            if marker.name in {"t0", "t1"}
        }
        non_null_pcs = [pc for pc in marker_pcs.values() if pc is not None]
        marker_defs_ok, marker_def_failures = marker_definition_status(item)
        record_failures: list[str] = []
        if item.warnings:
            record_failures.append("marker extraction warnings present: " + "; ".join(item.warnings))
        if named_delta != 0:
            record_failures.append(f"corrected t0/t1 marker delta is {named_delta}, expected 0")
        if len(marker_pcs) != 2:
            record_failures.append("t0/t1 marker PCs are incomplete")
        if len(set(non_null_pcs)) != 1:
            record_failures.append("t0/t1 marker labels do not resolve to the same PC")
        if item.timestamp_model_kind != "zero_cost_label_marker":
            record_failures.append(
                f"timestamp_model.kind is {item.timestamp_model_kind}, expected zero_cost_label_marker"
            )
        if item.timestamp_model_occupies_issue_slot is not False:
            record_failures.append("timestamp_model.occupies_issue_slot is not false")
        record_failures.extend(marker_def_failures)
        record = {
            "trace_path": item.trace_path.as_posix(),
            "mode": item.mode,
            "backend": item.backend,
            "marker_delta_cycles": named_delta,
            "marker_pcs": marker_pcs,
            "timestamp_model_kind": item.timestamp_model_kind,
            "timestamp_model_occupies_issue_slot": item.timestamp_model_occupies_issue_slot,
            "marker_definitions_zero_cost": marker_defs_ok,
            "warnings": list(item.warnings),
            "status": "PASS" if not record_failures else "FAIL",
        }
        if record_failures:
            record["failures"] = record_failures
            failures.append({"trace_path": item.trace_path.as_posix(), "failures": record_failures})
        records.append(record)

    if not candidates:
        failures.append(
            {
                "trace_path": None,
                "failures": ["missing checked-in real gem5 T00_BASELINE_MARKER trace evidence"],
            }
        )

    return {
        "status": "PASS" if candidates and not failures else "FAIL",
        "template_id": "T00_BASELINE_MARKER",
        "experiment_id": "t00-marker",
        "required": True,
        "contract": "zero_cost_label_pc_wrapper",
        "documented_assumption": (
            "TIMESTAMP_MARK is implemented as a zero-cost label-PC wrapper. Marker labels emit no instructions; "
            "the marker cycle is recovered from the first Exec-log instruction at the marker PC."
        ),
        "checked_real_gem5_t00_traces": len(candidates),
        "records": records,
        "failures": failures,
    }


def group_key_record(item: ExperimentAnalysis) -> dict[str, str]:
    return {
        "template_id": normalized_id(item.template_id),
        "instruction_id": normalized_id(item.instruction_id),
        "lmul": normalized_id(item.lmul),
    }


def repeat_key_record(item: ExperimentAnalysis) -> dict[str, str]:
    record = group_key_record(item)
    record["pair_instruction_id"] = normalized_id(item.pair_instruction_id)
    record["body_signature"] = stable_json(item.body)
    return record


def group_key_tuple(item: ExperimentAnalysis) -> tuple[str, str, str]:
    record = group_key_record(item)
    return (record["template_id"], record["instruction_id"], record["lmul"])


def sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def increment_template_instruction_lmul(
    counts: dict[str, dict[str, dict[str, int]]],
    item: ExperimentAnalysis,
) -> None:
    template_id, instruction_id, lmul = group_key_tuple(item)
    counts.setdefault(template_id, {}).setdefault(instruction_id, {}).setdefault(lmul, 0)
    counts[template_id][instruction_id][lmul] += 1


def counts_by_template_instruction_lmul(items: Iterable[ExperimentAnalysis]) -> dict[str, dict[str, dict[str, int]]]:
    counts: dict[str, dict[str, dict[str, int]]] = {}
    for item in items:
        increment_template_instruction_lmul(counts, item)
    return {
        template: {
            instruction: dict(sorted(lmuls.items()))
            for instruction, lmuls in sorted(instructions.items())
        }
        for template, instructions in sorted(counts.items())
    }


def group_tuple_to_record(group: tuple[str, str, str]) -> dict[str, str]:
    template_id, instruction_id, lmul = group
    return {
        "template_id": template_id,
        "instruction_id": instruction_id,
        "lmul": lmul,
    }


def discover_approval(root: Path) -> dict[str, Any]:
    candidates = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and path.name.lower() in APPROVAL_FILENAMES
        ),
        key=lambda path: path.as_posix(),
    )
    if not candidates:
        return {
            "status": "absent",
            "approved": False,
            "artifact_path": None,
            "artifacts": [],
        }

    artifacts: list[dict[str, Any]] = []
    approved = False
    for path in candidates:
        artifact: dict[str, Any] = {
            "path": path.as_posix(),
            "status": "present_unapproved",
            "approved": False,
            "machine_readable": path.suffix.lower() == ".json",
            "accepted_risk_ids": [],
        }
        try:
            if path.suffix.lower() == ".json":
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    status_value = str(
                        first_value(
                            data.get("status"),
                            data.get("human_approval_status"),
                            data.get("approval_status"),
                            "",
                        )
                    ).lower()
                    bool_value = first_value(data.get("approved"), data.get("human_approved"), data.get("human_approval"))
                    artifact["approved"] = bool_value is True or status_value in {"approved", "accepted", "pass", "passed"}
                    artifact["status"] = "approved" if artifact["approved"] else status_value or "present_unapproved"
                    artifact["accepted_risk_ids"] = sorted(accepted_risk_ids_from_document(data))
            else:
                text = path.read_text(encoding="utf-8").lower()
                has_positive = "approved: true" in text or "status: approved" in text or "human approval: approved" in text
                has_negative = "not approved" in text or "approval: absent" in text or "status: rejected" in text
                artifact["approved"] = has_positive and not has_negative
                artifact["status"] = "approved" if artifact["approved"] else "present_unapproved"
        except (OSError, json.JSONDecodeError) as exc:
            artifact["status"] = "unreadable"
            artifact["error"] = str(exc)
        approved = approved or bool(artifact["approved"])
        artifacts.append(artifact)

    return {
        "status": "approved" if approved else "present_unapproved",
        "approved": approved,
        "artifact_path": next((entry["path"] for entry in artifacts if entry.get("approved")), artifacts[0]["path"]),
        "artifacts": artifacts,
        "accepted_risk_ids": sorted(
            {
                risk_id
                for entry in artifacts
                if entry.get("approved")
                for risk_id in entry.get("accepted_risk_ids", [])
            }
        ),
    }


def summarize_repeat_groups(real_gem5_items: list[ExperimentAnalysis]) -> dict[str, Any]:
    groups: dict[str, list[ExperimentAnalysis]] = defaultdict(list)
    records_by_key: dict[str, dict[str, str]] = {}
    for item in real_gem5_items:
        record = repeat_key_record(item)
        key = stable_json(record)
        groups[key].append(item)
        records_by_key[key] = record

    summaries: list[dict[str, Any]] = []
    stable_group_keys: set[tuple[str, str, str]] = set()
    for key in sorted(groups):
        items = groups[key]
        if len(items) < 2:
            continue
        values = [item.corrected_primary_delta for item in items if item.corrected_primary_delta is not None]
        missing_delta_count = len(items) - len(values)
        value_summary: dict[str, Any] = {
            "values": values,
            "missing_delta_count": missing_delta_count,
        }
        if values:
            value_summary.update(
                {
                    "min": min(values),
                    "max": max(values),
                    "mean": mean(values),
                    "spread": max(values) - min(values),
                    "pstdev": pstdev(values) if len(values) > 1 else 0.0,
                }
            )
        stable = bool(values) and missing_delta_count == 0 and len(set(values)) == 1
        record = records_by_key[key]
        if stable:
            stable_group_keys.add((record["template_id"], record["instruction_id"], record["lmul"]))
        summaries.append(
            {
                "key": record,
                "trace_count": len(items),
                "trace_paths": [item.trace_path.as_posix() for item in sorted(items, key=lambda entry: entry.trace_path.as_posix())],
                "primary_delta_cycles": value_summary,
                "stable": stable,
                "status": "stable" if stable else "unstable",
            }
        )

    unstable = [group for group in summaries if not group["stable"]]
    return {
        "repeat_groups_total": len(summaries),
        "repeated_trace_total": sum(group["trace_count"] for group in summaries),
        "stable_repeat_groups": len(summaries) - len(unstable),
        "unstable_repeat_groups": len(unstable),
        "stable_template_instruction_lmul": [
            group_tuple_to_record(group) for group in sorted(stable_group_keys)
        ],
        "groups": summaries,
    }


def build_quality_inventory(analyses: list[ExperimentAnalysis], root: Path) -> dict[str, Any]:
    classified: dict[str, list[ExperimentAnalysis]] = {
        "synthetic": [],
        "real": [],
        "unknown": [],
        "conflict": [],
    }
    by_mode: Counter[str] = Counter()
    by_backend: Counter[str] = Counter()
    classification_conflicts: list[dict[str, Any]] = []

    for item in analyses:
        classification = trace_classification(item)
        classified[classification].append(item)
        by_mode[normalized_id(item.mode)] += 1
        by_backend[normalized_id(item.backend)] += 1
        mode = item.mode.lower()
        backend = item.backend.lower()
        if classification == "conflict":
            classification_conflicts.append(
                {
                    "kind": "mode_backend_conflict",
                    "trace_path": item.trace_path.as_posix(),
                    "mode": item.mode,
                    "backend": item.backend,
                }
            )
        if item.dry_run_trace and classification == "real":
            classification_conflicts.append(
                {
                    "kind": "real_trace_marked_dry_run",
                    "trace_path": item.trace_path.as_posix(),
                    "mode": item.mode,
                    "backend": item.backend,
                }
            )
        if "synthetic" in mode and "gem5" in backend:
            classification_conflicts.append(
                {
                    "kind": "synthetic_mode_with_gem5_backend",
                    "trace_path": item.trace_path.as_posix(),
                    "mode": item.mode,
                    "backend": item.backend,
                }
            )

    synthetic_items = classified["synthetic"]
    real_items = classified["real"]
    real_gem5_items = [item for item in real_items if is_real_gem5(item)]
    required_templates = sorted(
        {
            item.template_id
            for item in synthetic_items
            if item.template_id and item.template_id not in NON_REQUIRED_REAL_TEMPLATES
        }
    )
    required_groups = {
        group_key_tuple(item)
        for item in synthetic_items
        if item.template_id in required_templates
    }
    real_gem5_templates = sorted({item.template_id for item in real_gem5_items if item.template_id})
    real_gem5_groups = {
        group_key_tuple(item)
        for item in real_gem5_items
        if item.template_id in required_templates
    }
    missing_templates = sorted(set(required_templates) - set(real_gem5_templates))
    missing_groups = sorted(required_groups - real_gem5_groups)

    repeatability = summarize_repeat_groups(real_gem5_items)
    field_status = load_real_platform_field_status(root)
    marker_contract = build_marker_contract(real_gem5_items)
    stable_repeat_groups = {
        (entry["template_id"], entry["instruction_id"], entry["lmul"])
        for entry in repeatability["stable_template_instruction_lmul"]
    }
    missing_repeat_groups = sorted(required_groups - stable_repeat_groups)

    conflicts = list(classification_conflicts)
    for group in repeatability["groups"]:
        if not group["stable"]:
            conflicts.append(
                {
                    "kind": "unstable_repeat_delta",
                    "key": group["key"],
                    "primary_delta_cycles": group["primary_delta_cycles"],
                    "trace_paths": group["trace_paths"],
                }
            )

    approval = discover_approval(root)
    field_status_accepted = field_status_risks_accepted(field_status, approval)
    gate_checks = {
        "required_templates_covered_by_real_gem5": bool(required_templates) and not missing_templates,
        "required_template_instruction_lmul_covered_by_real_gem5": bool(required_groups) and not missing_groups,
        "stable_repeats_exist_for_required_groups": bool(required_groups) and not missing_repeat_groups,
        "real_platform_field_status_present": bool(field_status.get("exists"))
        and field_status.get("status") not in {"invalid", "no_records"},
        "required_llvm_field_status_clean_or_accepted": field_status.get("status") == "ready"
        or (bool(approval.get("approved")) and field_status_accepted),
        "marker_contract_valid": marker_contract.get("status") == "PASS",
        "no_unresolved_conflicts": not conflicts,
        "assumptions_documented": bool(QUALITY_ASSUMPTIONS),
        "explicit_human_approval": bool(approval.get("approved")),
    }
    failed_checks = [key for key, value in gate_checks.items() if not value]
    if marker_contract.get("status") != "PASS":
        confidence_level = "invalid_marker_contract"
    elif not field_status.get("exists") or field_status.get("status") in {"invalid", "no_records"}:
        confidence_level = "missing_real_platform_field_status"
    elif field_status.get("unresolved_total") and not field_status_accepted:
        confidence_level = "unresolved_llvm_field_status"
    elif conflicts:
        confidence_level = "conflicted"
    elif missing_templates or missing_groups:
        confidence_level = "insufficient_real_coverage"
    elif missing_repeat_groups:
        confidence_level = "insufficient_repeatability"
    elif not approval.get("approved"):
        confidence_level = "awaiting_human_approval"
    else:
        confidence_level = "approved_real_platform"

    return {
        "schema_version": 1,
        "result_root": root.as_posix(),
        "classification_basis": {
            "synthetic": "JSON mode/backend contains synthetic",
            "real": "JSON mode is real-platform or backend contains gem5",
            "path_used_for_classification": False,
        },
        "trace_totals": {
            "total": len(analyses),
            "synthetic": len(classified["synthetic"]),
            "real": len(classified["real"]),
            "real_gem5": len(real_gem5_items),
            "unknown": len(classified["unknown"]),
            "conflict": len(classified["conflict"]),
        },
        "counts": {
            "by_mode": sorted_counter(by_mode),
            "by_backend": sorted_counter(by_backend),
            "synthetic_by_template_instruction_lmul": counts_by_template_instruction_lmul(synthetic_items),
            "real_by_template_instruction_lmul": counts_by_template_instruction_lmul(real_items),
            "real_gem5_by_template_instruction_lmul": counts_by_template_instruction_lmul(real_gem5_items),
        },
        "coverage": {
            "required_template_source": "synthetic_trace_inventory_excluding_T00_BASELINE_MARKER",
            "required_templates": required_templates,
            "real_gem5_templates": real_gem5_templates,
            "covered_required_templates": sorted(set(required_templates) & set(real_gem5_templates)),
            "missing_real_templates": missing_templates,
            "required_template_instruction_lmul_total": len(required_groups),
            "real_gem5_required_template_instruction_lmul_total": len(real_gem5_groups & required_groups),
            "missing_real_template_instruction_lmul": [
                group_tuple_to_record(group) for group in missing_groups
            ],
        },
        "repeatability": {
            **repeatability,
            "missing_stable_repeat_template_instruction_lmul": [
                group_tuple_to_record(group) for group in missing_repeat_groups
            ],
        },
        "confidence": {
            "level": confidence_level,
            "failed_gate_checks": failed_checks,
        },
        "assumptions": {
            "status": "documented" if QUALITY_ASSUMPTIONS else "absent",
            "items": list(QUALITY_ASSUMPTIONS),
        },
        "conflicts": {
            "unresolved_total": len(conflicts),
            "items": conflicts,
        },
        "field_status": field_status,
        "marker_contract": marker_contract,
        "approval": approval,
        "risk_acceptance": {
            "field_status_unresolved_risks_accepted": field_status_accepted,
            "accepted_risk_ids": approval.get("accepted_risk_ids", []),
        },
        "gate": {
            "status": "PASS" if not failed_checks else "NOT_READY",
            "checks": gate_checks,
        },
    }


def group_records_by_template(groups: list[dict[str, str]]) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter(group["template_id"] for group in groups)
    return sorted(counter.items())


def append_group_table(lines: list[str], groups: list[dict[str, str]]) -> None:
    if not groups:
        lines.append("None.")
        return
    lines.append("| Template | Instruction | LMUL |")
    lines.append("| --- | --- | --- |")
    for group in groups:
        lines.append(
            f"| `{group['template_id']}` | `{group['instruction_id']}` | `{group['lmul']}` |"
        )


def render_quality_report(inventory: dict[str, Any]) -> str:
    trace_totals = inventory["trace_totals"]
    coverage = inventory["coverage"]
    repeatability = inventory["repeatability"]
    conflicts = inventory["conflicts"]
    field_status = inventory.get("field_status", {})
    marker_contract = inventory.get("marker_contract", {})
    risk_acceptance = inventory.get("risk_acceptance", {})
    approval = inventory["approval"]
    confidence = inventory["confidence"]
    gate = inventory["gate"]
    missing_groups = coverage["missing_real_template_instruction_lmul"]
    missing_repeat_groups = repeatability["missing_stable_repeat_template_instruction_lmul"]

    lines = [
        "# Experiment Quality Report",
        "",
        "Mode: real_platform_profile",
        f"Gate status: {gate['status']}",
        f"Confidence: {confidence['level']}",
        f"Human approval status: {approval['status']}",
        "",
        "This report is generated from trace inventory. Synthetic calibration traces remain separate from real-platform observations and do not count toward the real gate.",
        "",
        "## Approval Blockers",
        "",
    ]
    blockers: list[str] = []
    if not field_status.get("exists"):
        blockers.append(f"LLVM field-status artifact: missing `{field_status.get('path', FIELD_STATUS_FILENAME)}`.")
    elif field_status.get("status") == "invalid":
        blockers.append(
            "LLVM field-status artifact: invalid JSON"
            + (f" ({field_status.get('error')})." if field_status.get("error") else ".")
        )
    elif field_status.get("status") == "no_records":
        blockers.append("LLVM field-status artifact: no required LLVM-facing field records.")
    if field_status.get("missing_required_total"):
        blockers.append(
            f"LLVM field-status artifact: {field_status['missing_required_total']} required field records are missing."
        )
    field_status_accepted = bool(risk_acceptance.get("field_status_unresolved_risks_accepted"))
    if field_status.get("unresolved_total") and not field_status_accepted:
        unresolved_records = field_status.get("unresolved", [])
        counts = Counter(
            str(record.get("status", "unknown"))
            for record in unresolved_records
            if isinstance(record, dict)
        )
        count_text = ", ".join(f"{key}={value}" for key, value in counts.items()) if isinstance(counts, dict) else ""
        suffix = f" ({count_text})." if count_text else "."
        blockers.append(f"LLVM field-status unresolved risks: {field_status['unresolved_total']}{suffix}")
    if marker_contract.get("status") != "PASS":
        blockers.append("Marker contract: checked-in real gem5 T00 label-PC wrapper evidence is not valid.")
    if coverage["missing_real_templates"]:
        blockers.append(
            "Missing real gem5 template coverage: "
            + ", ".join(f"`{template}`" for template in coverage["missing_real_templates"])
            + "."
        )
    if missing_groups:
        blockers.append(f"Missing real gem5 template/instruction/LMUL groups: {len(missing_groups)}.")
    if missing_repeat_groups:
        blockers.append(f"Missing stable repeated real gem5 measurements: {len(missing_repeat_groups)} groups.")
    if conflicts["unresolved_total"]:
        blockers.append(f"Unresolved conflicts: {conflicts['unresolved_total']}.")
    if not approval.get("approved"):
        blockers.append("Explicit human approval artifact: absent or not approved.")
    if not blockers:
        blockers.append("None; all real-platform gate checks passed.")
    for blocker in blockers:
        lines.append(f"- {blocker}")

    lines.extend(["", "## Trace Inventory", ""])
    lines.append(f"Result root: `{inventory['result_root']}`")
    lines.append(f"Trace files analyzed: {trace_totals['total']}")
    lines.append(f"Synthetic traces: {trace_totals['synthetic']}")
    lines.append(f"Real-platform traces: {trace_totals['real']}")
    lines.append(f"Real gem5 traces: {trace_totals['real_gem5']}")
    lines.append(f"Unknown/conflicting traces: {trace_totals['unknown']} unknown, {trace_totals['conflict']} conflicting")
    lines.append("")
    lines.append("Classification uses JSON `mode` and `backend`; result paths are not used.")

    lines.extend(["", "## Coverage", ""])
    lines.append(
        "Required templates are inferred from the non-baseline synthetic latency/resource inventory: "
        + (", ".join(f"`{template}`" for template in coverage["required_templates"]) if coverage["required_templates"] else "none")
        + "."
    )
    lines.append(
        "Real gem5 templates covered: "
        + (", ".join(f"`{template}`" for template in coverage["real_gem5_templates"]) if coverage["real_gem5_templates"] else "none")
        + "."
    )
    lines.append("")
    lines.append("| Coverage field | Count |")
    lines.append("| --- | ---: |")
    lines.append(f"| Required template/instruction/LMUL groups | {coverage['required_template_instruction_lmul_total']} |")
    lines.append(f"| Covered required real gem5 groups | {coverage['real_gem5_required_template_instruction_lmul_total']} |")
    lines.append(f"| Missing required real gem5 groups | {len(missing_groups)} |")

    if missing_groups:
        lines.extend(["", "Missing required real gem5 groups by template:", ""])
        lines.append("| Template | Missing groups |")
        lines.append("| --- | ---: |")
        for template, count in group_records_by_template(missing_groups):
            lines.append(f"| `{template}` | {count} |")
        lines.extend(["", "Missing required real gem5 groups:", ""])
        append_group_table(lines, missing_groups)

    lines.extend(["", "## Repeatability", ""])
    lines.append(f"Repeat groups found: {repeatability['repeat_groups_total']}")
    lines.append(f"Stable repeat groups: {repeatability['stable_repeat_groups']}")
    lines.append(f"Unstable repeat groups: {repeatability['unstable_repeat_groups']}")
    if repeatability["groups"]:
        lines.extend(["", "| Template | Instruction | LMUL | Traces | Delta values | Status |"])
        lines.append("| --- | --- | --- | ---: | --- | --- |")
        for group in repeatability["groups"]:
            key = group["key"]
            values = group["primary_delta_cycles"]["values"]
            value_text = ", ".join(str(value) for value in values) if values else "none"
            lines.append(
                f"| `{key['template_id']}` | `{key['instruction_id']}` | `{key['lmul']}` | "
                f"{group['trace_count']} | `{value_text}` | {group['status']} |"
            )
    else:
        lines.append("No repeated real gem5 measurements are available.")
    if missing_repeat_groups:
        lines.extend(["", "Missing stable repeat groups by template:", ""])
        lines.append("| Template | Missing groups |")
        lines.append("| --- | ---: |")
        for template, count in group_records_by_template(missing_repeat_groups):
            lines.append(f"| `{template}` | {count} |")
        lines.extend(["", "Missing stable repeat groups:", ""])
        append_group_table(lines, missing_repeat_groups)

    lines.extend(["", "## Confidence", ""])
    lines.append(f"Computed confidence level: `{confidence['level']}`.")
    if confidence["failed_gate_checks"]:
        lines.append("Failed gate checks:")
        for check in confidence["failed_gate_checks"]:
            lines.append(f"- `{check}`")
    else:
        lines.append("No failed gate checks.")

    lines.extend(["", "## LLVM Field Status", ""])
    lines.append(f"Field-status artifact: `{field_status.get('path', FIELD_STATUS_FILENAME)}`")
    lines.append(f"Artifact present: {str(bool(field_status.get('exists'))).lower()}")
    if field_status.get("sha256"):
        lines.append(f"Artifact sha256: `{field_status['sha256']}`")
    lines.append(f"Field-status summary: `{field_status.get('status', 'missing')}`")
    lines.append(f"Required LLVM-facing fields: {', '.join(f'`{field}`' for field in REQUIRED_REAL_LLVM_FIELDS)}")
    lines.append(f"Status records: {field_status.get('records_total', 0)}")
    status_counts = field_status.get("status_counts")
    if isinstance(status_counts, dict) and status_counts:
        lines.append("")
        lines.append("| Field status | Count |")
        lines.append("| --- | ---: |")
        for status, count in status_counts.items():
            lines.append(f"| `{status}` | {count} |")
    unresolved = field_status.get("unresolved")
    if isinstance(unresolved, list) and unresolved:
        lines.extend(["", "Unresolved field-status risks:", ""])
        lines.append("| Risk ID | Instruction | LMUL | Field | Status | Reason |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for risk in unresolved:
            if not isinstance(risk, dict):
                continue
            reason = str(risk.get("reason", "")).replace("|", "\\|")
            lines.append(
                f"| `{risk.get('risk_id', '')}` | `{risk.get('instruction_id', 'unknown')}` | "
                f"`{risk.get('lmul', 'unknown')}` | `{risk.get('field', 'unknown')}` | "
                f"`{risk.get('status', 'unknown')}` | {reason} |"
            )
    else:
        lines.append("No unresolved field-status risks.")

    lines.extend(["", "## Marker Contract", ""])
    lines.append(f"Contract status: `{marker_contract.get('status', 'FAIL')}`")
    lines.append(f"Contract: `{marker_contract.get('contract', 'zero_cost_label_pc_wrapper')}`")
    if marker_contract.get("documented_assumption"):
        lines.append(str(marker_contract["documented_assumption"]))
    lines.append(f"Checked real gem5 T00 traces: {marker_contract.get('checked_real_gem5_t00_traces', 0)}")
    marker_failures = marker_contract.get("failures")
    if isinstance(marker_failures, list) and marker_failures:
        lines.append("")
        lines.append("| Trace | Failure |")
        lines.append("| --- | --- |")
        for failure in marker_failures:
            if not isinstance(failure, dict):
                continue
            trace = failure.get("trace_path") or "missing"
            for detail in failure.get("failures", []):
                detail_text = str(detail).replace("|", "\\|")
                lines.append(f"| `{trace}` | {detail_text} |")
    else:
        lines.append("No marker-contract failures.")

    lines.extend(["", "## Conflicts", ""])
    if conflicts["items"]:
        lines.append("| Kind | Detail |")
        lines.append("| --- | --- |")
        for conflict in conflicts["items"]:
            detail = conflict.get("trace_path") or stable_json(conflict.get("key", {}))
            lines.append(f"| `{conflict['kind']}` | `{detail}` |")
    else:
        lines.append("No unresolved conflicts detected in real-platform repeat or mode/backend classification data.")

    lines.extend(["", "## Assumptions", ""])
    for item in inventory["assumptions"]["items"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Human Approval", ""])
    if approval.get("artifact_path"):
        lines.append(f"Approval artifact: `{approval['artifact_path']}`")
        lines.append(f"Approval accepted by gate: {str(bool(approval.get('approved'))).lower()}")
    else:
        lines.append("Approval artifact: absent")
    lines.append(
        "The real gate cannot pass without clean field-status evidence or explicit per-risk acceptance, "
        "plus an approved human approval artifact tied to the real-platform inventory and field-status hashes."
    )

    lines.extend(["", "## Machine-Readable Sidecar", ""])
    lines.append(
        f"See `{inventory.get('inventory_path', 'results/common/real_platform_inventory.json')}` "
        "for the complete computed inventory, including exact missing group lists."
    )
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
        "Inference source status: non_circular_raw_marker_evidence",
        "",
        "Synthetic calibration compares only raw-inferred fields claimed by generated profiles against `config/rvv_timing_model.yaml`. Unknown or not-identifiable fields are explicit in the profiles and are not used as golden-equality claims.",
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
    lines.append("- `NumMicroOps`, `SingleIssue`, `ReadAdvance`, and separate writeback stage fields are recorded but unclaimed unless raw markers identify them.")
    lines.append("- Synthetic trace metadata is reference-only; it validates mismatches after raw marker inference and is not a source for claims.")
    lines.append("- Future real-platform gates must use coverage, stability, confidence, assumptions, conflict resolution, and human approval instead of golden equality.")
    return "\n".join(lines) + "\n"


def render_profile_yaml(profile: dict[str, Any]) -> str:
    return render_yaml(profile) + "\n"


def find_traces(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("**/trace.json"), key=lambda path: path.as_posix())


def is_run_result_branch(trace_path: Path, root: Path) -> bool:
    try:
        relative = trace_path.relative_to(root)
    except ValueError:
        return False
    return bool(relative.parts and RUN_RESULT_DIR_RE.fullmatch(relative.parts[0]))


def is_main_synthetic_calibration_trace(item: ExperimentAnalysis, root: Path) -> bool:
    return (
        item.mode.lower() == "synthetic_calibration"
        and item.backend.lower() == "synthetic_cmodel"
        and not is_run_result_branch(item.trace_path, root)
    )


def build_instruction_index(analyses: Iterable[ExperimentAnalysis]) -> dict[str, list[ExperimentAnalysis]]:
    by_instruction: dict[str, list[ExperimentAnalysis]] = {}
    for item in analyses:
        if item.instruction_id:
            by_instruction.setdefault(item.instruction_id, []).append(item)
        if item.pair_instruction_id:
            by_instruction.setdefault(item.pair_instruction_id, []).append(item)
    return by_instruction


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
    parser.add_argument(
        "--inventory",
        default=None,
        help="Real-platform machine-readable inventory path. Defaults next to --aggregate.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without changing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    trace_paths = find_traces(root)
    analyses = [analyze_trace(path) for path in trace_paths]
    synthetic_profile_analyses = [
        item for item in analyses if is_main_synthetic_calibration_trace(item, root)
    ]
    timing_config = load_timing_config(Path(args.config))
    config_instructions = timing_config.get("instructions") if isinstance(timing_config.get("instructions"), dict) else {}

    by_instruction = build_instruction_index(synthetic_profile_analyses)

    instruction_order = list(config_instructions) if isinstance(config_instructions, dict) else sorted(by_instruction)
    profiles: dict[str, dict[str, Any]] = {}
    for instruction_id in instruction_order:
        config_instr = config_instructions.get(instruction_id) if isinstance(config_instructions, dict) else None
        profiles[instruction_id] = build_profile(
            instruction_id,
            by_instruction.get(instruction_id, []),
            config_instr,
            by_instruction,
        )

    rows, failures = compare_profiles_to_config(profiles, timing_config)
    inventory = build_quality_inventory(analyses, root)
    inventory_path = Path(args.inventory) if args.inventory else Path(args.aggregate).with_name("real_platform_inventory.json")
    inventory["inventory_path"] = inventory_path.as_posix()

    writes: list[tuple[Path, str]] = []
    for item in analyses:
        writes.append((item.trace_path.parent / "analysis.md", render_experiment_markdown(item)))
    for instruction_id, profile in profiles.items():
        writes.append((root / instruction_id / "profile.yaml", render_profile_yaml(profile)))
    writes.append((inventory_path, json.dumps(inventory, indent=2, sort_keys=True) + "\n"))
    writes.append((Path(args.aggregate), render_quality_report(inventory)))
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
