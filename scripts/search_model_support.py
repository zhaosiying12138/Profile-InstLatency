#!/usr/bin/env python3
"""Search conservative RVV timing parameters from raw trace observations.

The search consumes ``trace.json`` files under ``results/**/experiments/**``
plus their sibling ``experiment.yaml`` metadata.  Marker deltas are used as the
only calibration evidence.  Synthetic golden timing fields may be carried
through as labeled references, but they are never used to claim a candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import product
from pathlib import Path
from typing import Any, Iterable


KNOWN_MARKER_PAIRS = (
    ("t0", "t1"),
    ("before", "after"),
    ("start", "end"),
    ("begin", "end"),
)

LMUL_ORDER = ("m1", "m2", "m4")
LMUL_VALUE = {"m1": 1, "m2": 2, "m4": 4, "m8": 8}
FIELD_ORDER = ("Latency", "ReleaseAtCycles", "ProcResource", "NumMicroOps", "SingleIssue")
BLOCKING_FIELD_STATUSES = (
    "conflict",
    "insufficient_evidence",
    "non_identifiable",
    "missing",
    "unknown",
    "invalid",
    "error",
    "not_set",
)
FIELD_VALUE_ATTR = {
    "Latency": "latency",
    "ReleaseAtCycles": "release_at_cycles",
    "ProcResource": "proc_resource",
    "NumMicroOps": "num_micro_ops",
    "SingleIssue": "single_issue",
}
PIPE_RESOURCE = {
    "any": "YuShuXinAnyVPipe",
    "pipe0": "YuShuXinVPipe0",
    "pipe1": "YuShuXinVPipe1",
}
PROC_RESOURCE_DOMAIN = ("any", "pipe0", "pipe1")
PIPE_LABEL_KEYS = (
    "pipe",
    "pipe_label",
    "proc_resource",
    "ProcResource",
    "resource",
    "resource_group",
    "unit",
)


@dataclass(frozen=True)
class Marker:
    name: str
    cycle: int
    index: int
    pc: str | None = None


@dataclass(frozen=True)
class RawObservation:
    trace_path: Path
    experiment_path: Path | None
    experiment_id: str
    instruction_id: str
    lmul: str
    template_id: str
    effective_template_id: str
    marker_pair: str
    delta_cycles: int
    marker_baseline_cycles: int
    parameters: dict[str, Any]
    body: dict[str, Any]
    pair_instruction_id: str | None
    raw_pipe_labels: tuple[str, ...]
    synthetic_reference: dict[str, Any]
    mode: str
    backend: str
    dry_run_trace: bool
    trace_sha256: str
    marker_start_pc_mod32: int | None = None


@dataclass(frozen=True)
class FormulaCandidate:
    base: int
    k: int
    residual: float


@dataclass(frozen=True)
class TimingCandidate:
    latency: int
    release_at_cycles: int
    proc_resource: str
    num_micro_ops: int
    single_issue: bool


@dataclass(frozen=True)
class CandidateSearchResult:
    candidates: tuple[TimingCandidate, ...]
    evidence: tuple[RawObservation, ...]
    skipped: tuple[str, ...]
    conflict_examples: tuple[dict[str, Any], ...]
    all_observations: tuple[RawObservation, ...] = ()
    t12_latency_constraints: tuple[T12LatencyConstraint, ...] = ()


@dataclass(frozen=True)
class CandidateCheck:
    observation: RawObservation
    status: str
    reason: str
    expected_delta: int | None = None
    observed_delta: int | None = None


@dataclass(frozen=True)
class T12LatencyConstraint:
    status: str
    reason: str
    evidence: tuple[RawObservation, ...]
    latency: int | None = None
    upper_bound: int | None = None
    filler_cadence: int | None = None
    clean_gaps: tuple[int, ...] = ()
    observed_cadence_gaps: tuple[int, ...] = ()


def t12_constraint_to_dict(constraint: T12LatencyConstraint) -> dict[str, Any]:
    return {
        "status": constraint.status,
        "reason": constraint.reason,
        "latency": constraint.latency,
        "upper_bound": constraint.upper_bound,
        "filler_cadence": constraint.filler_cadence,
        "clean_gaps": list(constraint.clean_gaps),
        "observed_cadence_gaps": list(constraint.observed_cadence_gaps),
    }


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
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value))


def dump_yaml(value: Any, indent: int = 0) -> str:
    spaces = " " * indent
    if isinstance(value, dict):
        if not value:
            return f"{spaces}{{}}"
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}{key}:")
                lines.append(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{spaces}{key}: {yaml_scalar(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return f"{spaces}[]"
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{spaces}-")
                lines.append(dump_yaml(item, indent + 2))
            else:
                lines.append(f"{spaces}- {yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{spaces}{yaml_scalar(value)}"


def profile_files_from_path(raw: str) -> list[Path]:
    path = Path(raw)
    if path.is_dir():
        direct_profile = path / "profile.yaml"
        if direct_profile.exists():
            return [direct_profile]
        return sorted(
            child / "profile.yaml"
            for child in path.iterdir()
            if child.is_dir() and (child / "profile.yaml").exists()
        )
    if path.exists() and path.name == "profile.yaml":
        return [path]
    return []


def experiment_trace_files(experiments_dir: Path) -> list[Path]:
    return sorted(experiments_dir.glob("*/trace.json"), key=lambda item: item.as_posix())


def trace_files_from_path(raw: str) -> list[Path]:
    path = Path(raw)
    if path.is_dir():
        experiments_dir = path / "experiments"
        if experiments_dir.exists():
            return experiment_trace_files(experiments_dir)
        traces: list[Path] = []
        for child in path.iterdir():
            child_experiments = child / "experiments"
            if child.is_dir() and child_experiments.exists():
                traces.extend(experiment_trace_files(child_experiments))
        return sorted(traces, key=lambda item: item.as_posix())
    if not path.exists():
        return []
    if path.name == "profile.yaml":
        experiments_dir = path.parent / "experiments"
        if experiments_dir.exists():
            return experiment_trace_files(experiments_dir)
        return []
    if path.name == "trace.json" or path.suffix == ".json":
        return [path]
    return []


def load_profiles(paths: list[str]) -> list[Path]:
    loaded: list[Path] = []
    for raw in paths:
        loaded.extend(profile_files_from_path(raw))
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


def pc_mod32(pc: str | None) -> int | None:
    if pc is None:
        return None
    try:
        return int(str(pc), 0) % 32
    except ValueError:
        return None


def named_marker_deltas(markers: tuple[Marker, ...], baseline: int) -> list[tuple[str, int, int | None]]:
    by_name: dict[str, Marker] = {}
    for marker in markers:
        by_name.setdefault(marker.name, marker)
    deltas: list[tuple[str, int, int | None]] = []
    for left_name, right_name in KNOWN_MARKER_PAIRS:
        left = by_name.get(left_name)
        right = by_name.get(right_name)
        if left is not None and right is not None:
            deltas.append((f"{left_name}/{right_name}", right.cycle - left.cycle - baseline, pc_mod32(left.pc)))
    return deltas


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
    observation = trace_doc.get("observation")
    observation_value = observation.get(key) if isinstance(observation, dict) else None
    return first_value(
        trace_metadata(trace_doc).get(key),
        trace_doc.get(key),
        observation_value,
        nested_get(experiment_doc, experiment_path) if experiment_path else experiment_doc.get(key),
    )


def body_int(observation: RawObservation, *keys: str) -> int | None:
    for key in keys:
        for container in (observation.parameters, observation.body):
            value = container.get(key)
            result = int_or_none(value)
            if result is not None:
                return result
    return None


def body_bool(observation: RawObservation, *keys: str) -> bool | None:
    for key in keys:
        for container in (observation.parameters, observation.body):
            if key in container:
                return bool_or_false(container.get(key))
    return None


def t11_has_latency_evidence(observation: RawObservation) -> bool:
    if observation.effective_template_id != "T11_SELF_RAW_CHAIN":
        return False
    return any(
        value is True
        for value in (
            body_bool(observation, "latency_evidence"),
            body_bool(observation, "true_raw_chain"),
            body_bool(observation, "chainable"),
        )
    )


def t11_latency_skip_reason(observation: RawObservation) -> str:
    return (
        "T11 skipped:not_latency_evidence;"
        f"body.latency_evidence={body_bool(observation, 'latency_evidence')};"
        f"body.true_raw_chain={body_bool(observation, 'true_raw_chain')};"
        f"body.chainable={body_bool(observation, 'chainable')};"
        "use T12_CONSUMER_RAW_GAP with an implemented bypass/read-advance model"
    )


def experiment_token(instruction_id: str) -> str:
    return instruction_id.replace("_", "-")


def summarize_counts(values: Iterable[int]) -> str:
    ordered = sorted(dict.fromkeys(values))
    return "[" + ",".join(str(value) for value in ordered) + "]"


def t12_latency_follow_up(items: Iterable[RawObservation], instruction_id: str, lmul: str) -> str:
    t12_items = [item for item in items if item.effective_template_id == "T12_CONSUMER_RAW_GAP"]
    consumers = sorted({str(item.body.get("consumer") or item.pair_instruction_id or "unknown") for item in t12_items})
    gaps = [gap for item in t12_items if (gap := body_int(item, "filler_count")) is not None]
    consumer_text = ",".join(consumers) if consumers else "result-kind-default-consumer"
    gap_text = summarize_counts(gaps) if gaps else "k0..k40"
    return (
        "Run/interpret template=T12_CONSUMER_RAW_GAP "
        f"instruction={instruction_id} lmul={lmul} consumer={consumer_text} gaps={gap_text}; "
        "register_policy=producer destination from metadata with independent vadd_vv fillers; "
        "collect gap0 plus contiguous clean-prefix gaps with defensible filler cadence before claiming Latency."
    )


def t20_startup_slope_groups(items: Iterable[RawObservation]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[RawObservation]] = defaultdict(list)
    for item in items:
        if item.effective_template_id != "T20_PAIRWISE_PIPE_CLASSIFICATION" or item.pair_instruction_id is None:
            continue
        grouped[(item.pair_instruction_id, t20_register_policy(item))].append(item)
    groups: list[dict[str, Any]] = []
    for pair_instruction_id, register_policy in sorted(grouped):
        by_count: dict[int, list[int]] = defaultdict(list)
        register_reuse = False
        for item in grouped[(pair_instruction_id, register_policy)]:
            count = body_int(item, "iterations", "pair_count", "sample_count")
            if count is None or count <= 0:
                continue
            by_count[count].append(item.delta_cycles)
            register_reuse = register_reuse or bool_or_false(item.body.get("register_reuse"))
        counts = sorted(by_count)
        group: dict[str, Any] = {
            "pair_instruction_id": pair_instruction_id,
            "register_policy": register_policy,
            "counts": counts,
            "deltas_by_count": {str(count): sorted(by_count[count]) for count in counts},
            "register_reuse": register_reuse,
        }
        if register_reuse:
            group["status"] = "skipped_register_reuse"
            groups.append(group)
            continue
        if len(counts) >= 2:
            left = counts[0]
            right = counts[-1]
            delta_left = min(by_count[left])
            delta_right = min(by_count[right])
            slope = (delta_right - delta_left) / (right - left)
            group.update(
                {
                    "status": "startup_slope_recorded",
                    "startup_cycles": delta_left - (left * slope),
                    "slope_cycles_per_pair": slope,
                }
            )
        else:
            group["status"] = "single_count_non_identifiable"
        groups.append(group)
    return groups


def t20_proc_resource_follow_up(items: Iterable[RawObservation], instruction_id: str, lmul: str) -> str:
    groups = t20_startup_slope_groups(items)
    pairs = [str(group["pair_instruction_id"]) for group in groups] or ["peer-instruction"]
    counts = sorted({count for group in groups for count in group.get("counts", [])})
    examples = ", ".join(
        f"t20-{experiment_token(instruction_id)}-{experiment_token(pair)}-{lmul}-{{n2,n3,n4,n6}}"
        for pair in pairs[:4]
    )
    return (
        "Run generated T20 pair-count sweep "
        f"template=T20_PAIRWISE_PIPE_CLASSIFICATION instruction={instruction_id} lmul={lmul} "
        f"pairs={','.join(pairs[:8])} observed_counts={summarize_counts(counts) if counts else '[]'} "
        f"required_counts=n2,n3,n4,n6; experiment_ids={examples}; "
        "register_policy=prefer register_reuse=false, annotate/exclude reused cases."
    )


def compact_parameters(
    trace_doc: dict[str, Any],
    experiment_doc: dict[str, Any],
    body_doc: dict[str, Any],
    pair_instruction_id: str | None,
) -> dict[str, Any]:
    parameters: dict[str, Any] = {}
    raw_parameters = experiment_doc.get("parameters")
    if isinstance(raw_parameters, dict):
        parameters.update(raw_parameters)
    observation = trace_doc.get("observation")
    if isinstance(observation, dict):
        for key in ("iterations", "filler_count", "pair_instruction_id"):
            if observation.get(key) is not None:
                parameters[key] = observation[key]
    for key in ("iterations", "stream_length", "sample_count", "filler_count", "pair_count"):
        if body_doc.get(key) is not None:
            parameters[key] = body_doc[key]
    if pair_instruction_id is not None:
        parameters["pair_instruction_id"] = pair_instruction_id
    return parameters


def normalize_pipe_label(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    label = str(value)
    if not label:
        return None
    reverse = {resource: pipe for pipe, resource in PIPE_RESOURCE.items()}
    return reverse.get(label, label)


def collect_raw_pipe_labels(trace_doc: dict[str, Any]) -> tuple[str, ...]:
    labels: list[str] = []
    entries = trace_doc.get("entries")
    if isinstance(entries, list):
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for key in PIPE_LABEL_KEYS:
                label = normalize_pipe_label(entry.get(key))
                if label is not None:
                    labels.append(label)

    observation = trace_doc.get("observation")
    observation_source = str(observation.get("source", "")).lower() if isinstance(observation, dict) else ""
    if isinstance(observation, dict) and "synthetic" not in observation_source:
        for key in PIPE_LABEL_KEYS:
            label = normalize_pipe_label(observation.get(key))
            if label is not None:
                labels.append(label)

    backend_mode = f"{trace_doc.get('backend', '')} {trace_doc.get('mode', '')}".lower()
    if "synthetic" not in backend_mode:
        for key in PIPE_LABEL_KEYS:
            label = normalize_pipe_label(trace_doc.get(key))
            if label is not None:
                labels.append(label)
    return tuple(dict.fromkeys(labels))


def trace_document_mode(trace_doc: dict[str, Any]) -> str:
    return str(first_value(trace_doc.get("mode"), trace_metadata(trace_doc).get("mode"), "unknown"))


def trace_document_backend(trace_doc: dict[str, Any]) -> str:
    return str(first_value(trace_doc.get("backend"), trace_metadata(trace_doc).get("backend"), "unknown"))


def trace_document_matches(
    trace_doc: dict[str, Any],
    *,
    mode: str | None,
    backend: str | None,
    include_dry_run: bool,
) -> bool:
    if mode is not None and trace_document_mode(trace_doc) != mode:
        return False
    if backend is not None and trace_document_backend(trace_doc) != backend:
        return False
    real_filter = mode == "real_platform_profile" or backend == "gem5_minor"
    if real_filter and not include_dry_run and bool_or_false(trace_doc.get("dry_run_trace")):
        return False
    return True


def load_trace_observations(
    trace_path: Path,
    trace_doc: dict[str, Any] | None = None,
) -> tuple[list[RawObservation], list[str]]:
    warnings: list[str] = []
    if trace_doc is None:
        try:
            trace_doc = load_trace_document(trace_path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            return [], [f"{trace_path.as_posix()}: {error}"]

    experiment_path = trace_path.with_name("experiment.yaml")
    experiment_doc = parse_yamlish(experiment_path) if experiment_path.exists() else {}
    entries = trace_doc.get("entries")
    markers = extract_markers(entries if isinstance(entries, list) else [])
    baseline = int_or_none(trace_doc.get("marker_baseline_cycles")) or 0
    deltas = named_marker_deltas(markers, baseline)
    if not deltas:
        warnings.append(f"{trace_path.as_posix()}: no known marker pair delta found")
        return [], warnings

    instruction_id = metadata_value(trace_doc, experiment_doc, "instruction_id", ("instruction", "id"))
    lmul = metadata_value(trace_doc, experiment_doc, "lmul", ("parameters", "lmul"))
    template_id = metadata_value(trace_doc, experiment_doc, "template_id")
    if instruction_id is None or lmul is None or template_id is None:
        warnings.append(f"{trace_path.as_posix()}: missing instruction_id, lmul, or template_id")
        return [], warnings

    body_doc = experiment_doc.get("body") if isinstance(experiment_doc.get("body"), dict) else {}
    pair_instruction_id = first_value(
        nested_get(trace_doc, ("observation", "pair_instruction_id")),
        nested_get(experiment_doc, ("pair_instruction", "id")),
        body_doc.get("consumer") if isinstance(body_doc, dict) else None,
    )
    scaling_shape = first_value(
        body_doc.get("scaling_shape") if isinstance(body_doc, dict) else None,
        nested_get(experiment_doc, ("scaling", "shape")),
        nested_get(trace_doc, ("observation", "scaling_shape")),
    )
    template_text = str(template_id)
    effective_template_id = str(scaling_shape) if template_text == "T30_LMUL_SCALING" and scaling_shape else template_text
    synthetic = trace_metadata(trace_doc).get("synthetic")
    synthetic_reference = dict(synthetic) if isinstance(synthetic, dict) else {}
    mode = trace_document_mode(trace_doc)
    backend = trace_document_backend(trace_doc)
    dry_run_trace = bool_or_false(trace_doc.get("dry_run_trace"))
    try:
        trace_sha256 = file_sha256(trace_path)
    except OSError:
        trace_sha256 = ""
    parameters = compact_parameters(
        trace_doc,
        experiment_doc,
        dict(body_doc),
        str(pair_instruction_id) if pair_instruction_id is not None else None,
    )
    raw_pipe_labels = collect_raw_pipe_labels(trace_doc)
    experiment_id = str(
        first_value(
            trace_doc.get("experiment_id"),
            experiment_doc.get("experiment_id"),
            trace_path.parent.name,
        )
    )

    observations: list[RawObservation] = []
    for marker_pair, delta, marker_start_pc_mod32 in deltas:
        observations.append(
            RawObservation(
                trace_path=trace_path,
                experiment_path=experiment_path if experiment_path.exists() else None,
                experiment_id=experiment_id,
                instruction_id=str(instruction_id),
                lmul=str(lmul),
                template_id=template_text,
                effective_template_id=effective_template_id,
                marker_pair=marker_pair,
                delta_cycles=delta,
                marker_baseline_cycles=baseline,
                parameters=dict(parameters),
                body=dict(body_doc),
                pair_instruction_id=str(pair_instruction_id) if pair_instruction_id is not None else None,
                raw_pipe_labels=raw_pipe_labels,
                synthetic_reference=synthetic_reference,
                mode=mode,
                backend=backend,
                dry_run_trace=dry_run_trace,
                trace_sha256=trace_sha256,
                marker_start_pc_mod32=marker_start_pc_mod32,
            )
        )
    return observations, warnings


def load_observations(
    paths: list[str],
    *,
    mode: str | None = None,
    backend: str | None = None,
    include_dry_run: bool = False,
) -> tuple[list[RawObservation], list[Path], list[str]]:
    trace_paths: list[Path] = []
    for raw in paths:
        trace_paths.extend(trace_files_from_path(raw))
    trace_paths = sorted(dict.fromkeys(trace_paths), key=lambda item: item.as_posix())

    observations: list[RawObservation] = []
    filtered_trace_paths: list[Path] = []
    warnings: list[str] = []
    for trace_path in trace_paths:
        try:
            trace_doc = load_trace_document(trace_path)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            warnings.append(f"{trace_path.as_posix()}: {error}")
            continue
        if not trace_document_matches(trace_doc, mode=mode, backend=backend, include_dry_run=include_dry_run):
            continue
        filtered_trace_paths.append(trace_path)
        loaded, trace_warnings = load_trace_observations(trace_path, trace_doc)
        observations.extend(loaded)
        warnings.extend(trace_warnings)
    return observations, filtered_trace_paths, warnings


def observation_key(observation: RawObservation) -> tuple[str, str]:
    return observation.instruction_id, observation.lmul


def mirrored_t20_peer_observation(observation: RawObservation) -> RawObservation | None:
    if observation.effective_template_id != "T20_PAIRWISE_PIPE_CLASSIFICATION":
        return None
    if observation.pair_instruction_id is None or observation.pair_instruction_id == observation.instruction_id:
        return None
    return replace(
        observation,
        instruction_id=observation.pair_instruction_id,
        pair_instruction_id=observation.instruction_id,
    )


def lmul_sort_key(lmul: str) -> tuple[int, str]:
    return LMUL_VALUE.get(lmul, 999), lmul


def evidence_entry(observation: RawObservation, detail: str) -> str:
    return (
        f"{observation.experiment_id}:{observation.effective_template_id}:"
        f"pair={observation.marker_pair}:delta={observation.delta_cycles}:{detail}"
        f" @ {observation.trace_path.as_posix()}"
    )


def unique_observations(items: Iterable[RawObservation]) -> tuple[RawObservation, ...]:
    seen: set[tuple[str, str, str, str, int]] = set()
    result: list[RawObservation] = []
    for item in items:
        key = (
            item.trace_path.as_posix(),
            item.experiment_id,
            item.effective_template_id,
            item.marker_pair,
            item.delta_cycles,
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return tuple(result)


def bounded_integer_result(
    field: str,
    candidates: set[int],
    used_evidence: list[str],
    skipped_evidence: list[str],
    max_value: int,
    *,
    no_evidence_reason: str,
) -> dict[str, Any]:
    evidence = used_evidence + skipped_evidence
    result: dict[str, Any] = {
        "field": field,
        "range": f"0..{max_value}",
        "evidence": evidence,
        "constraint_count": len(used_evidence),
    }
    if not used_evidence:
        result.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "candidates": [],
                "candidate_count": 0,
                "reason": no_evidence_reason,
            }
        )
    elif not candidates:
        result.update(
            {
                "status": "conflict",
                "value": None,
                "candidates": [],
                "candidate_count": 0,
                "reason": "No value in the bounded search range satisfies all raw marker constraints.",
            }
        )
    elif len(candidates) == 1:
        value = next(iter(candidates))
        result.update(
            {
                "status": "exact_fit",
                "value": value,
                "candidates": [value],
                "candidate_count": 1,
            }
        )
    else:
        result.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "candidates": sorted(candidates),
                "candidate_count": len(candidates),
                "reason": "Available template timings leave multiple bounded candidates.",
            }
        )
    return result


def enumerate_latency(items: list[RawObservation], max_value: int) -> dict[str, Any]:
    candidates = set(range(max_value + 1))
    used: list[str] = []
    skipped: list[str] = []

    for item in items:
        shape = item.effective_template_id
        if shape == "T11_SELF_RAW_CHAIN":
            iterations = body_int(item, "iterations", "chain_length", "sample_count")
            if iterations is None or iterations <= 1:
                skipped.append(evidence_entry(item, "T11 skipped:missing_iterations"))
                continue
            intervals = iterations - 1
            candidates &= {value for value in candidates if item.delta_cycles == intervals * value}
            used.append(evidence_entry(item, f"T11 expected delta=(iterations-1)*Latency;iterations={iterations}"))
        elif shape == "T12_CONSUMER_RAW_GAP":
            skipped.append(evidence_entry(item, "T12 recorded:handled_by_shared_candidate_simulator"))

    return bounded_integer_result(
        "Latency",
        candidates,
        used,
        skipped,
        max_value,
        no_evidence_reason="No T11/T12/T30 raw marker constraint is available for latency.",
    )


def enumerate_release(items: list[RawObservation], max_value: int) -> dict[str, Any]:
    candidates = set(range(max_value + 1))
    used: list[str] = []
    skipped: list[str] = []

    for item in items:
        shape = item.effective_template_id
        if shape != "T10_INDEPENDENT_STREAM_THROUGHPUT":
            continue
        iterations = body_int(item, "iterations", "stream_length", "sample_count")
        if iterations is None or iterations <= 1:
            skipped.append(evidence_entry(item, "T10 skipped:missing_iterations"))
            continue
        intervals = iterations - 1
        candidates &= {value for value in candidates if item.delta_cycles == intervals * value}
        used.append(evidence_entry(item, f"T10 expected delta=(iterations-1)*ReleaseAtCycles;iterations={iterations}"))

    return bounded_integer_result(
        "ReleaseAtCycles",
        candidates,
        used,
        skipped,
        max_value,
        no_evidence_reason="No T10/T30 raw marker constraint is available for release/occupancy.",
    )


def proc_resource_for_label(label: str) -> str:
    return PIPE_RESOURCE.get(label, label)


def release_value(release_results: dict[tuple[str, str], dict[str, Any]], instruction_id: str, lmul: str) -> int | None:
    result = release_results.get((instruction_id, lmul))
    if not result or result.get("status") != "exact_fit":
        return None
    return int_or_none(result.get("value"))


def pipe_choices(label: str) -> tuple[int, ...]:
    if label == "pipe0":
        return (0,)
    if label == "pipe1":
        return (1,)
    if label == "any":
        return (0, 1)
    return (0, 1)


def same_resource(left: str, right: str) -> bool:
    return left == right and left in {"pipe0", "pipe1"}


def issue_occupancy(candidate: TimingCandidate) -> int:
    return max(candidate.release_at_cycles, candidate.num_micro_ops)


def t20_resource_cycles(left: TimingCandidate, right: TimingCandidate, left_pipe: int, right_pipe: int) -> int:
    left_release = max(1, left.release_at_cycles)
    right_release = max(1, right.release_at_cycles)
    if left_pipe == right_pipe:
        return left_release + right_release
    return max(left_release, right_release)


def t20_issue_cycles(left: TimingCandidate, right: TimingCandidate) -> int:
    left_ops = max(1, left.num_micro_ops)
    right_ops = max(1, right.num_micro_ops)
    if left.single_issue or right.single_issue:
        return left_ops + right_ops
    return max(left_ops, right_ops)


def expected_t20_pair_cycles(left: TimingCandidate, right: TimingCandidate) -> int:
    issue_cycles = t20_issue_cycles(left, right)
    best: int | None = None
    for left_pipe in pipe_choices(left.proc_resource):
        for right_pipe in pipe_choices(right.proc_resource):
            pair_cycles = max(t20_resource_cycles(left, right, left_pipe, right_pipe), issue_cycles)
            if best is None or pair_cycles < best:
                best = pair_cycles
    return best if best is not None else issue_cycles


def expected_t21_pair_cycles(candidate: TimingCandidate) -> int:
    vector_issue_cycles = issue_occupancy(candidate)
    if candidate.single_issue:
        return vector_issue_cycles + 1
    return max(vector_issue_cycles, 1)


def candidate_to_dict(candidate: TimingCandidate) -> dict[str, Any]:
    return {
        "Latency": candidate.latency,
        "ReleaseAtCycles": candidate.release_at_cycles,
        "ProcResource": proc_resource_for_label(candidate.proc_resource),
        "NumMicroOps": candidate.num_micro_ops,
        "SingleIssue": candidate.single_issue,
    }


def candidate_field_value(candidate: TimingCandidate, field: str) -> Any:
    if field == "Latency":
        return candidate.latency
    if field == "ReleaseAtCycles":
        return candidate.release_at_cycles
    if field == "ProcResource":
        return proc_resource_for_label(candidate.proc_resource)
    if field == "NumMicroOps":
        return candidate.num_micro_ops
    if field == "SingleIssue":
        return candidate.single_issue
    raise KeyError(field)


def candidate_sort_key(candidate: TimingCandidate) -> tuple[int, int, str, int, int]:
    return (
        candidate.latency,
        candidate.release_at_cycles,
        candidate.proc_resource,
        candidate.num_micro_ops,
        int(candidate.single_issue),
    )


def candidate_cost(candidate: TimingCandidate) -> tuple[int, int, int, int, int]:
    return (
        candidate.release_at_cycles + candidate.latency + candidate.num_micro_ops + int(candidate.single_issue),
        candidate.release_at_cycles,
        candidate.latency,
        candidate.num_micro_ops,
        int(candidate.single_issue),
    )


def direct_interval_candidates(
    items: list[RawObservation],
    shape: str,
    body_keys: tuple[str, ...],
    max_value: int,
) -> set[int]:
    boundary_candidates = boundary_corrected_direct_interval_candidates(items, shape, body_keys, max_value)
    if boundary_candidates is not None:
        return boundary_candidates
    points: list[tuple[int, int]] = []
    for item in items:
        if item.effective_template_id != shape:
            continue
        if shape == "T11_SELF_RAW_CHAIN" and not t11_has_latency_evidence(item):
            continue
        iterations = body_int(item, *body_keys)
        if iterations is None or iterations <= 1:
            continue
        intervals = iterations - 1
        points.append((intervals, item.delta_cycles))
    if not points:
        return set(range(max_value + 1))
    candidates: set[int] = set()
    for value in range(max_value + 1):
        offsets = {delta - intervals * value for intervals, delta in points}
        if len(offsets) == 1:
            candidates.add(value)
    return candidates


def vcpop_m4_boundary_model_item(item: RawObservation, shape: str) -> bool:
    return item.instruction_id == "vcpop_m" and item.lmul == "m4" and item.effective_template_id == shape


def boundary_start_pc_mod32(item: RawObservation) -> int | None:
    if item.marker_start_pc_mod32 is not None:
        return item.marker_start_pc_mod32
    return body_int(item, "target_start_pc_mod32", "start_pc_mod32")


def boundary_body_instruction_count(item: RawObservation, shape: str, iterations: int) -> int | None:
    metadata_count = body_int(item, "body_instruction_count", "timed_body_instruction_count")
    if metadata_count is not None and metadata_count > 0:
        return metadata_count
    if shape == "T10_INDEPENDENT_STREAM_THROUGHPUT":
        return iterations
    if shape == "T21_PAIR_WITH_SCALAR":
        return iterations * 2
    return None


def boundary_fetch_penalty(item: RawObservation, shape: str, iterations: int) -> int | None:
    start_mod32 = boundary_start_pc_mod32(item)
    body_instruction_count = boundary_body_instruction_count(item, shape, iterations)
    if start_mod32 is None or body_instruction_count is None or body_instruction_count <= 0:
        return None
    return 4 * ((start_mod32 + 4 * (body_instruction_count - 1)) // 32)


def boundary_corrected_direct_interval_candidates(
    items: list[RawObservation],
    shape: str,
    body_keys: tuple[str, ...],
    max_value: int,
) -> set[int] | None:
    if shape != "T10_INDEPENDENT_STREAM_THROUGHPUT":
        return None
    shape_items = [item for item in items if item.effective_template_id == shape]
    if not shape_items:
        return None
    if not all(item.instruction_id == "vcpop_m" and item.lmul == "m4" for item in shape_items):
        return None
    if not any(boundary_start_pc_mod32(item) is not None for item in shape_items):
        return None

    points: list[tuple[int, int]] = []
    for item in shape_items:
        iterations = body_int(item, *body_keys)
        if iterations is None or iterations <= 1:
            return set()
        penalty = boundary_fetch_penalty(item, shape, iterations)
        if penalty is None:
            return set()
        points.append((iterations - 1, item.delta_cycles - penalty))
    candidates: set[int] = set()
    for value in range(max_value + 1):
        if all(delta == intervals * value for intervals, delta in points):
            candidates.add(value)
    return candidates


def all_timing_candidates(
    max_value: int,
    *,
    latencies: set[int] | None = None,
    releases: set[int] | None = None,
) -> tuple[TimingCandidate, ...]:
    candidates: list[TimingCandidate] = []
    latency_values = sorted(latencies if latencies is not None else set(range(max_value + 1)))
    release_values = sorted(releases if releases is not None else set(range(max_value + 1)))
    for latency in latency_values:
        for release in release_values:
            for proc_resource in PROC_RESOURCE_DOMAIN:
                for num_micro_ops in range(1, 5):
                    for single_issue in (False, True):
                        candidates.append(TimingCandidate(latency, release, proc_resource, num_micro_ops, single_issue))
    return tuple(candidates)


def t20_per_pair_observed(item: RawObservation) -> int | None:
    iterations = body_int(item, "iterations", "pair_count", "sample_count")
    if iterations is None or iterations <= 0:
        return None
    return item.delta_cycles


def t21_per_pair_observed(item: RawObservation) -> int | None:
    iterations = body_int(item, "iterations", "pair_count", "sample_count")
    if iterations is None or iterations <= 0:
        return None
    if item.delta_cycles % iterations != 0:
        return None
    return item.delta_cycles // iterations


def first_metadata_value(item: RawObservation, *keys: str) -> Any:
    for key in keys:
        for container in (item.body, item.parameters):
            if key in container and container.get(key) is not None:
                return container.get(key)
    return None


def t20_register_policy(item: RawObservation) -> str:
    policy = first_metadata_value(
        item,
        "register_policy",
        "source_register_policy",
        "src_register_policy",
        "destination_register_policy",
        "dst_register_policy",
        "register_allocation_policy",
    )
    return str(policy) if policy is not None else "unspecified"


def t20_observation_group_key(item: RawObservation) -> tuple[str, str, str | None, str]:
    return (item.instruction_id, item.lmul, item.pair_instruction_id, t20_register_policy(item))


def matching_t20_group(item: RawObservation, group_items: Iterable[RawObservation]) -> tuple[RawObservation, ...]:
    key = t20_observation_group_key(item)
    return tuple(
        candidate
        for candidate in group_items
        if candidate.effective_template_id == "T20_PAIRWISE_PIPE_CLASSIFICATION"
        and t20_observation_group_key(candidate) == key
    )


def t20_min_delta_by_count(items: Iterable[RawObservation]) -> dict[int, int]:
    by_count: dict[int, list[int]] = defaultdict(list)
    for item in items:
        count = body_int(item, "iterations", "pair_count", "sample_count")
        if count is None or count <= 0:
            continue
        by_count[count].append(item.delta_cycles)
    return {count: min(deltas) for count, deltas in by_count.items()}


def t20_slope_matches(count_to_delta: dict[int, int], slope: int) -> bool:
    if len(count_to_delta) < 2:
        return False
    offsets = {delta - count * slope for count, delta in count_to_delta.items()}
    return len(offsets) == 1


def internal_proc_resource_label(value: Any) -> str | None:
    label = normalize_pipe_label(value)
    if label in PROC_RESOURCE_DOMAIN:
        return label
    return None


def proc_resource_domain_labels(values: Iterable[Any]) -> tuple[str, ...]:
    labels = {label for value in values if (label := internal_proc_resource_label(value)) is not None}
    return tuple(label for label in PROC_RESOURCE_DOMAIN if label in labels)


def format_observation_key(key: tuple[str, str]) -> str:
    return f"{key[0]}:{key[1]}"


def public_proc_resource_labels(labels: Iterable[str]) -> list[str]:
    return [proc_resource_for_label(label) for label in labels]


def t20_usable_for_proc_resource(item: RawObservation) -> bool:
    disambiguation = item.body.get("resource_disambiguation")
    if isinstance(disambiguation, dict) and "usable_for_proc_resource" in disambiguation:
        return bool_or_false(disambiguation.get("usable_for_proc_resource"))
    return True


def canonical_t20_proc_group_key(item: RawObservation) -> tuple[tuple[str, str], tuple[str, str], str] | None:
    if item.effective_template_id != "T20_PAIRWISE_PIPE_CLASSIFICATION" or item.pair_instruction_id is None:
        return None
    left = (item.instruction_id, item.lmul)
    right = (item.pair_instruction_id, item.lmul)
    if right < left:
        left, right = right, left
    return left, right, t20_register_policy(item)


def t20_proc_resource_constraints(
    observations: Iterable[RawObservation],
    release_values: dict[tuple[str, str], int],
    candidate_domains: dict[tuple[str, str], tuple[str, ...]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[tuple[str, str], tuple[str, str], str], list[RawObservation]] = defaultdict(list)
    for item in observations:
        key = canonical_t20_proc_group_key(item)
        if key is not None:
            grouped[key].append(item)

    usable: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for (left_key, right_key, register_policy), group in sorted(
        grouped.items(),
        key=lambda entry: (
            format_observation_key(entry[0][0]),
            format_observation_key(entry[0][1]),
            entry[0][2],
        ),
    ):
        evidence = [evidence_entry(item, "global_proc_resource:T20") for item in unique_observations(group)]
        base_detail: dict[str, Any] = {
            "left": format_observation_key(left_key),
            "right": format_observation_key(right_key),
            "register_policy": register_policy,
            "evidence": evidence,
        }
        if not all(t20_usable_for_proc_resource(item) for item in group):
            skipped.append({**base_detail, "status": "skipped_metadata_not_usable"})
            continue
        if any(bool_or_false(item.body.get("register_reuse")) for item in group):
            skipped.append({**base_detail, "status": "skipped_register_reuse"})
            continue
        count_to_delta = t20_min_delta_by_count(group)
        counts = sorted(count_to_delta)
        if len(counts) < 2:
            skipped.append({**base_detail, "status": "skipped_single_count", "counts": counts})
            continue
        empty_domains = [
            format_observation_key(key)
            for key in (left_key, right_key)
            if not candidate_domains.get(key)
        ]
        if empty_domains:
            skipped.append(
                {
                    **base_detail,
                    "status": "skipped_empty_candidate_domain",
                    "empty_candidate_domains": empty_domains,
                    "counts": counts,
                }
            )
            continue
        missing_releases = [
            format_observation_key(key)
            for key in (left_key, right_key)
            if release_values.get(key) is None
        ]
        if missing_releases:
            skipped.append(
                {
                    **base_detail,
                    "status": "skipped_missing_release",
                    "missing_release_values": missing_releases,
                    "counts": counts,
                }
            )
            continue

        first_count = counts[0]
        last_count = counts[-1]
        slope = Fraction(
            count_to_delta[last_count] - count_to_delta[first_count],
            last_count - first_count,
        )
        offsets = {Fraction(count_to_delta[count]) - count * slope for count in counts}
        usable.append(
            {
                **base_detail,
                "status": "usable",
                "left_key": left_key,
                "right_key": right_key,
                "counts": counts,
                "min_deltas_by_count": {str(count): count_to_delta[count] for count in counts},
                "slope": slope,
                "slope_cycles_per_pair": int(slope) if slope.denominator == 1 else float(slope),
                "startup_affine": len(offsets) == 1,
                "startup_cycles": (
                    int(next(iter(offsets))) if len(offsets) == 1 and next(iter(offsets)).denominator == 1 else None
                ),
                "left_release": release_values[left_key],
                "right_release": release_values[right_key],
            }
        )
    return usable, skipped


def expected_t20_proc_resource_slope(
    left_label: str,
    right_label: str,
    left_release: int,
    right_release: int,
) -> int:
    left = TimingCandidate(0, left_release, left_label, 1, False)
    right = TimingCandidate(0, right_release, right_label, 1, False)
    return expected_t20_pair_cycles(left, right)


def proc_resource_constraint_matches(
    constraint: dict[str, Any],
    assignment: dict[tuple[str, str], str],
) -> bool:
    if not constraint.get("startup_affine"):
        return False
    left_key = constraint["left_key"]
    right_key = constraint["right_key"]
    expected = expected_t20_proc_resource_slope(
        assignment[left_key],
        assignment[right_key],
        int(constraint["left_release"]),
        int(constraint["right_release"]),
    )
    return Fraction(expected) == constraint["slope"]


def proc_resource_components(
    constraints: list[dict[str, Any]],
) -> list[set[tuple[str, str]]]:
    graph: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
    for constraint in constraints:
        left = constraint["left_key"]
        right = constraint["right_key"]
        graph[left].add(right)
        graph[right].add(left)
    components: list[set[tuple[str, str]]] = []
    seen: set[tuple[str, str]] = set()
    for root in sorted(graph):
        if root in seen:
            continue
        stack = [root]
        component: set[tuple[str, str]] = set()
        while stack:
            key = stack.pop()
            if key in component:
                continue
            component.add(key)
            stack.extend(sorted(graph[key] - component))
        seen.update(component)
        components.append(component)
    return components


def proc_resource_solution_dict(solution: dict[tuple[str, str], str]) -> dict[str, str]:
    return {
        format_observation_key(key): proc_resource_for_label(solution[key])
        for key in sorted(solution)
    }


def mirror_proc_resource_label(label: str) -> str:
    if label == "pipe0":
        return "pipe1"
    if label == "pipe1":
        return "pipe0"
    return label


def mirror_proc_resource_solution(solution: dict[tuple[str, str], str]) -> dict[tuple[str, str], str]:
    return {key: mirror_proc_resource_label(label) for key, label in solution.items()}


def proc_resource_solution_sort_key(solution: dict[tuple[str, str], str]) -> tuple[tuple[str, str], ...]:
    return tuple((format_observation_key(key), solution[key]) for key in sorted(solution))


def pure_global_pipe_mirror_solutions(
    solutions: list[dict[tuple[str, str], str]],
    solution_count: int,
) -> tuple[dict[tuple[str, str], str], list[dict[tuple[str, str], str]]] | None:
    if solution_count != 2 or len(solutions) != 2:
        return None
    first, second = solutions
    if mirror_proc_resource_solution(first) != second:
        return None
    ordered = sorted(solutions, key=proc_resource_solution_sort_key)
    return ordered[0], ordered[1:]


def proc_resource_mirror_assumption(
    canonical_solution: dict[tuple[str, str], str],
    alternate_solutions: list[dict[tuple[str, str], str]],
    solution_count: int,
) -> dict[str, Any]:
    return {
        "type": "global_pipe_label_mirror",
        "equivalence": "pipe0_pipe1_global_swap",
        "scope": "connected_t20_component",
        "canonicalization": "lexicographically_smallest_internal_assignment",
        "solution_count_before_canonicalization": solution_count,
        "canonical_assignment": proc_resource_solution_dict(canonical_solution),
        "alternate_assignments": [
            proc_resource_solution_dict(solution) for solution in alternate_solutions
        ],
    }


def solve_global_proc_resources(
    observations: Iterable[RawObservation],
    release_values: dict[tuple[str, str], int],
    candidate_domains: dict[tuple[str, str], tuple[str, ...]],
    *,
    max_reported_solutions: int = 32,
) -> dict[str, Any]:
    normalized_domains = {
        key: proc_resource_domain_labels(values)
        for key, values in candidate_domains.items()
    }
    constraints, skipped = t20_proc_resource_constraints(observations, release_values, normalized_domains)
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    conflict_constraints: list[dict[str, Any]] = []
    symmetry_breaking_assumptions: list[dict[str, Any]] = []

    for component in proc_resource_components(constraints):
        component_constraints = [
            constraint
            for constraint in constraints
            if constraint["left_key"] in component and constraint["right_key"] in component
        ]
        nodes = sorted(component)
        solutions: list[dict[tuple[str, str], str]] = []
        survivors: dict[tuple[str, str], set[str]] = {key: set() for key in nodes}
        domain_product = product(*(normalized_domains[key] for key in nodes))
        solution_count = 0
        for values in domain_product:
            assignment = dict(zip(nodes, values))
            if not all(proc_resource_constraint_matches(constraint, assignment) for constraint in component_constraints):
                continue
            solution_count += 1
            for key, label in assignment.items():
                survivors[key].add(label)
            if len(solutions) < max_reported_solutions:
                solutions.append(dict(assignment))

        evidence = [
            entry
            for constraint in component_constraints
            for entry in constraint.get("evidence", [])
        ]
        public_solutions = [proc_resource_solution_dict(solution) for solution in solutions]
        if solution_count == 0:
            public_constraints = [
                {
                    "left": constraint["left"],
                    "right": constraint["right"],
                    "register_policy": constraint["register_policy"],
                    "counts": constraint["counts"],
                    "slope_cycles_per_pair": constraint["slope_cycles_per_pair"],
                }
                for constraint in component_constraints
            ]
            conflict_constraints.extend(public_constraints)
            for key in nodes:
                rows[key] = {
                    "status": "conflict",
                    "value": None,
                    "candidates": [],
                    "candidate_count": 0,
                    "constraint_count": sum(
                        1
                        for constraint in component_constraints
                        if key in {constraint["left_key"], constraint["right_key"]}
                    ),
                    "evidence": evidence,
                    "reason": (
                        "No global ProcResource assignment satisfies all usable startup-free "
                        "T20 pair slopes and exact ReleaseAtCycles values."
                    ),
                    "global_solution_count": 0,
                    "global_candidates": [],
                    "surviving_candidates": [],
                    "conflict_constraints": public_constraints,
                }
            continue

        mirror_solution = pure_global_pipe_mirror_solutions(solutions, solution_count)
        canonical_solution: dict[tuple[str, str], str] | None = None
        mirror_assumption: dict[str, Any] | None = None
        if mirror_solution is not None:
            canonical_solution, alternate_solutions = mirror_solution
            mirror_assumption = proc_resource_mirror_assumption(
                canonical_solution,
                alternate_solutions,
                solution_count,
            )
            symmetry_breaking_assumptions.append(mirror_assumption)

        for key in nodes:
            pre_canonical_surviving = tuple(label for label in PROC_RESOURCE_DOMAIN if label in survivors[key])
            if canonical_solution is not None:
                surviving = (canonical_solution[key],)
            else:
                surviving = pre_canonical_surviving
            public_surviving = public_proc_resource_labels(surviving)
            exact = len(surviving) == 1
            if exact and mirror_assumption is not None:
                reason = (
                    "Pure global ProcResource pipe-label mirror assignments satisfy the usable "
                    "startup-free T20 pair slopes; a deterministic pipe0/pipe1 orientation was "
                    "canonicalized as a symmetry-breaking assumption."
                )
            elif exact:
                reason = (
                    "Unique global ProcResource assignment satisfies usable startup-free T20 "
                    "pair slopes and exact ReleaseAtCycles values."
                )
            else:
                reason = (
                    "Multiple mirror/global ProcResource assignments satisfy the usable "
                    "startup-free T20 pair slopes, so the row remains non-identifiable."
                )
            row = {
                "status": "exact_fit" if exact else "non_identifiable",
                "value": proc_resource_for_label(surviving[0]) if exact else None,
                "candidates": public_surviving,
                "candidate_count": len(public_surviving),
                "constraint_count": sum(
                    1
                    for constraint in component_constraints
                    if key in {constraint["left_key"], constraint["right_key"]}
                ),
                "evidence": evidence,
                "reason": reason,
                "global_solution_count": solution_count,
                "global_candidates": public_solutions,
                "surviving_candidates": public_surviving,
            }
            pre_canonical_public = public_proc_resource_labels(pre_canonical_surviving)
            if mirror_assumption is not None:
                row["symmetry_breaking_assumption"] = mirror_assumption
                row["pre_canonical_surviving_candidates"] = pre_canonical_public
            rows[key] = row

    public_constraints = [
        {
            "left": constraint["left"],
            "right": constraint["right"],
            "register_policy": constraint["register_policy"],
            "counts": constraint["counts"],
            "slope_cycles_per_pair": constraint["slope_cycles_per_pair"],
            "startup_affine": constraint["startup_affine"],
        }
        for constraint in constraints
    ]
    return {
        "rows": rows,
        "usable_constraints": public_constraints,
        "skipped_constraints": skipped,
        "conflict_constraints": conflict_constraints,
        "symmetry_breaking_assumptions": symmetry_breaking_assumptions,
    }


def t20_peer_candidates(
    item: RawObservation,
    candidate_options: dict[tuple[str, str], tuple[TimingCandidate, ...]],
    fixed_candidates: dict[tuple[str, str], TimingCandidate],
) -> tuple[TimingCandidate, ...]:
    if item.pair_instruction_id is None:
        return ()
    key = (item.pair_instruction_id, item.lmul)
    fixed = fixed_candidates.get(key)
    if fixed is not None:
        return (fixed,)
    return candidate_options.get(key, ())


def check_t20_candidate_group(
    item: RawObservation,
    candidate: TimingCandidate,
    candidate_options: dict[tuple[str, str], tuple[TimingCandidate, ...]],
    fixed_candidates: dict[tuple[str, str], TimingCandidate],
    group_items: Iterable[RawObservation],
) -> CandidateCheck:
    if item.pair_instruction_id is None:
        return CandidateCheck(item, "skipped", "T20 skipped:missing_pair_instruction", None, item.delta_cycles)
    group = matching_t20_group(item, group_items)
    if any(bool_or_false(member.body.get("register_reuse")) for member in group):
        return CandidateCheck(
            item,
            "skipped",
            (
                "T20 skipped:register_reuse_true_without_model;"
                f"instruction={item.instruction_id};lmul={item.lmul};pair={item.pair_instruction_id};"
                f"register_policy={t20_register_policy(item)}"
            ),
            None,
            item.delta_cycles,
        )
    count_to_delta = t20_min_delta_by_count(group)
    counts = sorted(count_to_delta)
    if len(counts) < 2:
        return CandidateCheck(
            item,
            "skipped",
            (
                "T20 skipped:single_count_non_identifiable;"
                f"instruction={item.instruction_id};lmul={item.lmul};pair={item.pair_instruction_id};"
                f"register_policy={t20_register_policy(item)};counts={counts}"
            ),
            None,
            item.delta_cycles,
        )
    peers = t20_peer_candidates(item, candidate_options, fixed_candidates)
    if not peers:
        return CandidateCheck(
            item,
            "skipped",
            (
                "T20 skipped:missing_peer_candidate_options;"
                f"instruction={item.instruction_id};lmul={item.lmul};pair={item.pair_instruction_id};"
                f"counts={counts}"
            ),
            None,
            item.delta_cycles,
        )
    matching_slopes = sorted(
        {
            expected_t20_pair_cycles(candidate, peer)
            for peer in peers
            if t20_slope_matches(count_to_delta, expected_t20_pair_cycles(candidate, peer))
        }
    )
    if matching_slopes:
        return CandidateCheck(
            item,
            "match",
            (
                "T20 startup_free_slope matched;"
                f"instruction={item.instruction_id};lmul={item.lmul};pair={item.pair_instruction_id};"
                f"register_policy={t20_register_policy(item)};counts={counts};"
                f"expected_slopes={matching_slopes}"
            ),
            matching_slopes[0],
            item.delta_cycles,
        )
    expected_slopes = sorted({expected_t20_pair_cycles(candidate, peer) for peer in peers})
    return CandidateCheck(
        item,
        "mismatch",
        (
            "T20 startup_free_slope mismatch;"
            f"instruction={item.instruction_id};lmul={item.lmul};pair={item.pair_instruction_id};"
            f"register_policy={t20_register_policy(item)};counts={counts};"
            f"min_deltas={[count_to_delta[count] for count in counts]};expected_slopes={expected_slopes}"
        ),
        expected_slopes[0] if expected_slopes else None,
        item.delta_cycles,
    )
