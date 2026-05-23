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
from dataclasses import dataclass
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


@dataclass(frozen=True)
class CandidateCheck:
    observation: RawObservation
    status: str
    reason: str
    expected_delta: int | None = None
    observed_delta: int | None = None


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
        return sorted(path.rglob("profile.yaml"), key=lambda item: item.as_posix())
    if path.exists() and path.name == "profile.yaml":
        return [path]
    return []


def trace_files_from_path(raw: str) -> list[Path]:
    path = Path(raw)
    if path.is_dir():
        return sorted(path.rglob("trace.json"), key=lambda item: item.as_posix())
    if not path.exists():
        return []
    if path.name == "profile.yaml":
        experiments_dir = path.parent / "experiments"
        if experiments_dir.exists():
            return sorted(experiments_dir.rglob("trace.json"), key=lambda item: item.as_posix())
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


def named_marker_deltas(markers: tuple[Marker, ...], baseline: int) -> list[tuple[str, int]]:
    by_name: dict[str, Marker] = {}
    for marker in markers:
        by_name.setdefault(marker.name, marker)
    deltas: list[tuple[str, int]] = []
    for left_name, right_name in KNOWN_MARKER_PAIRS:
        left = by_name.get(left_name)
        right = by_name.get(right_name)
        if left is not None and right is not None:
            deltas.append((f"{left_name}/{right_name}", right.cycle - left.cycle - baseline))
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
        "implement bypass/read-advance readiness model before claiming Latency."
    )


def t20_startup_slope_groups(items: Iterable[RawObservation]) -> list[dict[str, Any]]:
    grouped: dict[str, list[RawObservation]] = defaultdict(list)
    for item in items:
        if item.effective_template_id != "T20_PAIRWISE_PIPE_CLASSIFICATION" or item.pair_instruction_id is None:
            continue
        grouped[item.pair_instruction_id].append(item)
    groups: list[dict[str, Any]] = []
    for pair_instruction_id in sorted(grouped):
        by_count: dict[int, list[int]] = defaultdict(list)
        register_reuse = False
        for item in grouped[pair_instruction_id]:
            count = body_int(item, "iterations", "pair_count", "sample_count")
            if count is None or count <= 0:
                continue
            by_count[count].append(item.delta_cycles)
            register_reuse = register_reuse or bool_or_false(item.body.get("register_reuse"))
        counts = sorted(by_count)
        group: dict[str, Any] = {
            "pair_instruction_id": pair_instruction_id,
            "counts": counts,
            "deltas_by_count": {str(count): sorted(by_count[count]) for count in counts},
            "register_reuse": register_reuse,
        }
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
    for marker_pair, delta in deltas:
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
            skipped.append(evidence_entry(item, "T12 recorded:not_used_without_bypass_gap_simulator"))

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


def same_resource(left: str, right: str) -> bool:
    if "any" in (left, right):
        return True
    return left == right


def issue_occupancy(candidate: TimingCandidate) -> int:
    return max(candidate.release_at_cycles, candidate.num_micro_ops)


def expected_t20_pair_cycles(left: TimingCandidate, right: TimingCandidate) -> int:
    if same_resource(left.proc_resource, right.proc_resource):
        return issue_occupancy(left) + issue_occupancy(right)
    return max(issue_occupancy(left), issue_occupancy(right))


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


def expected_delta_for_observation(
    item: RawObservation,
    candidate: TimingCandidate,
    candidate_lookup: dict[tuple[str, str], TimingCandidate],
) -> tuple[int | None, str]:
    shape = item.effective_template_id
    if shape == "T10_INDEPENDENT_STREAM_THROUGHPUT":
        iterations = body_int(item, "iterations", "stream_length", "sample_count")
        if iterations is None or iterations <= 1:
            return None, "T10 skipped:missing_iterations"
        return None, (
            "T10 constrained collectively by delta=startup+(iterations-1)*ReleaseAtCycles;"
            f"iterations={iterations}"
        )
    if shape == "T11_SELF_RAW_CHAIN":
        if not t11_has_latency_evidence(item):
            return None, t11_latency_skip_reason(item)
        iterations = body_int(item, "iterations", "chain_length", "sample_count")
        if iterations is None or iterations <= 1:
            return None, "T11 skipped:missing_iterations"
        return None, (
            "T11 constrained collectively by delta=startup+(iterations-1)*Latency;"
            f"iterations={iterations}"
        )
    if shape == "T12_CONSUMER_RAW_GAP":
        consumer = item.body.get("consumer") or item.pair_instruction_id or "unknown"
        gap = body_int(item, "filler_count")
        return None, (
            "T12 non_identifiable:no implemented bypass/read-advance model;"
            f"template=T12_CONSUMER_RAW_GAP;instruction={item.instruction_id};"
            f"lmul={item.lmul};consumer={consumer};gap={gap};"
            "follow_up=run T12 consumer-gap sweep k=0..40 and implement "
            "producer-result-to-consumer readiness model"
        )
    if shape == "T20_PAIRWISE_PIPE_CLASSIFICATION":
        iterations = body_int(item, "iterations", "pair_count", "sample_count")
        if item.pair_instruction_id is None or iterations is None or iterations <= 0:
            return None, "T20 skipped:missing_pair_or_iterations"
        return None, (
            "T20 startup+slope recorded:current checked-in real traces have one usable "
            "pair-count per instruction pair/LMUL, so startup cannot be separated from "
            f"slope;template=T20_PAIRWISE_PIPE_CLASSIFICATION;instruction={item.instruction_id};"
            f"lmul={item.lmul};pair={item.pair_instruction_id};counts=[{iterations}];"
            "follow_up=run generated pair-count sweep n2,n3,n4,n6 with register_reuse=false "
            "when available"
        )
    if shape == "T21_PAIR_WITH_SCALAR":
        iterations = body_int(item, "iterations", "pair_count", "sample_count")
        if iterations is None or iterations <= 0:
            return None, "T21 skipped:missing_iterations"
        if item.delta_cycles % iterations != 0:
            return None, (
                "T21 non_identifiable:marker delta is not divisible by pair count, "
                "so scalar-pair issue occupancy cannot be used as a hard constraint"
            )
        return iterations * expected_t21_pair_cycles(candidate), (
            f"T21 expected delta=iterations*scalar_pair_cycles;iterations={iterations}"
        )
    return None, f"{shape} recorded:not_used_by_candidate_simulator"


def check_candidate(
    item: RawObservation,
    candidate: TimingCandidate,
    candidate_lookup: dict[tuple[str, str], TimingCandidate],
) -> CandidateCheck:
    expected, reason = expected_delta_for_observation(item, candidate, candidate_lookup)
    if expected is None:
        return CandidateCheck(item, "skipped", reason, None, item.delta_cycles)
    if expected == item.delta_cycles:
        return CandidateCheck(item, "match", reason, expected, item.delta_cycles)
    return CandidateCheck(item, "mismatch", reason, expected, item.delta_cycles)


def check_candidate_against_options(
    item: RawObservation,
    candidate: TimingCandidate,
    candidate_options: dict[tuple[str, str], tuple[TimingCandidate, ...]],
    fixed_candidates: dict[tuple[str, str], TimingCandidate],
) -> CandidateCheck:
    local_lookup = dict(fixed_candidates)
    local_lookup[(item.instruction_id, item.lmul)] = candidate
    return check_candidate(item, candidate, local_lookup)


def select_minimal_candidates(candidates: Iterable[TimingCandidate]) -> tuple[TimingCandidate, ...]:
    ordered = sorted(candidates, key=lambda item: (candidate_cost(item), candidate_sort_key(item)))
    if not ordered:
        return ()
    best_cost = candidate_cost(ordered[0])
    return tuple(candidate for candidate in ordered if candidate_cost(candidate) == best_cost)


def candidate_result_for_group(
    key: tuple[str, str],
    items: list[RawObservation],
    all_group_items: dict[tuple[str, str], list[RawObservation]],
    max_value: int,
    base_candidates: dict[tuple[str, str], tuple[TimingCandidate, ...]] | None = None,
) -> CandidateSearchResult:
    if base_candidates is None:
        base_candidates = {key: all_timing_candidates(max_value)}
    candidate_lookup: dict[tuple[str, str], TimingCandidate] = {}
    viable: list[TimingCandidate] = []
    evidence: list[RawObservation] = []
    skipped: list[str] = []
    conflicts: list[dict[str, Any]] = []

    for candidate in base_candidates.get(key, ()):
        candidate_lookup[key] = candidate
        ok = True
        for item in items:
            check = check_candidate(item, candidate, candidate_lookup)
            if check.status == "skipped":
                skipped.append(evidence_entry(item, check.reason))
                continue
            evidence.append(item)
            if check.status == "mismatch":
                ok = False
                if len(conflicts) < 16:
                    conflicts.append(
                        {
                            "experiment_id": item.experiment_id,
                            "template_id": item.effective_template_id,
                            "trace": item.trace_path.as_posix(),
                            "candidate": candidate_to_dict(candidate),
                            "expected_delta": check.expected_delta,
                            "observed_delta": check.observed_delta,
                            "reason": check.reason,
                        }
                    )
                break
        if ok:
            viable.append(candidate)
    return CandidateSearchResult(
        candidates=select_minimal_candidates(viable),
        evidence=unique_observations(evidence),
        skipped=tuple(dict.fromkeys(skipped)),
        conflict_examples=tuple(conflicts),
        all_observations=tuple(items),
    )


def solve_candidate_sets(
    grouped: dict[tuple[str, str], list[RawObservation]],
    max_value: int,
    *,
    max_passes: int = 8,
) -> dict[tuple[str, str], CandidateSearchResult]:
    base: dict[tuple[str, str], tuple[TimingCandidate, ...]] = {
        key: all_timing_candidates(
            max_value,
            latencies=direct_interval_candidates(
                items,
                "T11_SELF_RAW_CHAIN",
                ("iterations", "chain_length", "sample_count"),
                max_value,
            ),
            releases=direct_interval_candidates(
                items,
                "T10_INDEPENDENT_STREAM_THROUGHPUT",
                ("iterations", "stream_length", "sample_count"),
                max_value,
            ),
        )
        for key, items in grouped.items()
    }
    results: dict[tuple[str, str], CandidateSearchResult] = {}
    for _pass in range(max_passes):
        changed = False
        candidate_lookup = {
            key: candidates[0]
            for key, candidates in base.items()
            if len(candidates) == 1
        }
        next_base: dict[tuple[str, str], tuple[TimingCandidate, ...]] = {}
        for key, items in grouped.items():
            viable: list[TimingCandidate] = []
            evidence: list[RawObservation] = [
                item
                for item in items
                if item.effective_template_id
                in {"T10_INDEPENDENT_STREAM_THROUGHPUT", "T11_SELF_RAW_CHAIN"}
                and (item.effective_template_id != "T11_SELF_RAW_CHAIN" or t11_has_latency_evidence(item))
            ]
            skipped: list[str] = []
            conflicts: list[dict[str, Any]] = []
            if not base[key]:
                constrained_items = [
                    item
                    for item in items
                    if item.effective_template_id
                    in {
                        "T10_INDEPENDENT_STREAM_THROUGHPUT",
                        "T11_SELF_RAW_CHAIN",
                        "T20_PAIRWISE_PIPE_CLASSIFICATION",
                        "T21_PAIR_WITH_SCALAR",
                    }
                ]
                results[key] = CandidateSearchResult(
                    candidates=(),
                    evidence=tuple(constrained_items),
                    skipped=(),
                    conflict_examples=(
                        {
                            "experiment_id": constrained_items[0].experiment_id,
                            "template_id": constrained_items[0].effective_template_id,
                            "trace": constrained_items[0].trace_path.as_posix(),
                            "reason": "Direct interval constraints produced an empty candidate domain.",
                        },
                    )
                    if constrained_items
                    else (),
                    all_observations=tuple(items),
                )
                next_base[key] = ()
                continue
            for candidate in base[key]:
                ok = True
                for item in items:
                    check = check_candidate_against_options(item, candidate, base, candidate_lookup)
                    if check.status == "skipped":
                        skipped.append(evidence_entry(item, check.reason))
                        continue
                    evidence.append(item)
                    if check.status == "mismatch":
                        ok = False
                        if len(conflicts) < 16:
                            conflicts.append(
                                {
                                    "experiment_id": item.experiment_id,
                                    "template_id": item.effective_template_id,
                                    "trace": item.trace_path.as_posix(),
                                    "candidate": candidate_to_dict(candidate),
                                    "expected_delta": check.expected_delta,
                                    "observed_delta": check.observed_delta,
                                    "reason": check.reason,
                                }
                            )
                        break
                if ok:
                    viable.append(candidate)
            minimal = select_minimal_candidates(viable)
            next_base[key] = minimal
            results[key] = CandidateSearchResult(
                candidates=minimal,
                evidence=unique_observations(evidence),
                skipped=tuple(dict.fromkeys(skipped)),
                conflict_examples=tuple(conflicts),
                all_observations=tuple(items),
            )
            if set(minimal) != set(base[key]):
                changed = True
        base = next_base
        if not changed:
            break
    return results


def direct_interval_domain_conflict(result: CandidateSearchResult) -> bool:
    return any(
        str(item.get("reason", "")).startswith("Direct interval constraints produced an empty candidate domain")
        for item in result.conflict_examples
    )


def non_affine_stream_follow_up(observations: Iterable[RawObservation]) -> str:
    stream_points: list[str] = []
    for item in observations:
        if item.effective_template_id != "T10_INDEPENDENT_STREAM_THROUGHPUT":
            continue
        iterations = body_int(item, "iterations", "stream_length", "sample_count")
        if iterations is None:
            continue
        stream_points.append(f"n{iterations}=delta{item.delta_cycles}")
    suffix = "; observed_points=" + ",".join(stream_points[:16]) if stream_points else ""
    return (
        "Add a focused T10 stream-length and alignment sweep before claiming LLVM-facing "
        "issue fields; vary N around the first non-affine point, marker PC alignment, "
        "scalar destination policy, and source register policy."
        + suffix
    )


def candidate_field_result(
    field: str,
    result: CandidateSearchResult,
    *,
    max_value: int,
    non_identifiable: bool = False,
) -> dict[str, Any]:
    evidence = [
        evidence_entry(item, f"candidate_simulator:{field}")
        for item in result.evidence
        if item.effective_template_id != "T12_CONSUMER_RAW_GAP"
    ]
    evidence.extend(result.skipped[:16])
    values = sorted(
        {candidate_field_value(candidate, field) for candidate in result.candidates},
        key=lambda item: str(item),
    )
    if field in {"Latency", "ReleaseAtCycles"}:
        candidate_domain: Any = f"0..{max_value}"
    elif field == "ProcResource":
        candidate_domain = [proc_resource_for_label(label) for label in PROC_RESOURCE_DOMAIN]
    elif field == "NumMicroOps":
        candidate_domain = [1, 2, 3, 4]
    else:
        candidate_domain = [False, True]

    record: dict[str, Any] = {
        "field": field,
        "candidate_domain": candidate_domain,
        "evidence": evidence,
        "constraint_count": len(result.evidence),
        "candidate_count": len(values),
        "candidates": values,
    }
    if field in {"Latency", "ReleaseAtCycles"}:
        record["range"] = f"0..{max_value}"

    if field == "Latency":
        true_t11 = any(t11_has_latency_evidence(item) for item in result.all_observations)
        has_t12 = any(item.effective_template_id == "T12_CONSUMER_RAW_GAP" for item in result.all_observations)
        has_placeholder_t11 = any(
            item.effective_template_id == "T11_SELF_RAW_CHAIN" and not t11_has_latency_evidence(item)
            for item in result.all_observations
        )
        if not true_t11 and (has_t12 or has_placeholder_t11):
            first = result.all_observations[0] if result.all_observations else None
            instruction_id = first.instruction_id if first is not None else "unknown"
            lmul = first.lmul if first is not None else "unknown"
            record.update(
                {
                    "status": "non_identifiable",
                    "value": None,
                    "reason": (
                        "T11 observations for this row are non-chainable placeholders or absent; "
                        "T12 consumer-gap observations exist but the shared simulator has no "
                        "implemented bypass/read-advance model, so Latency is not identifiable."
                    ),
                    "follow_up": t12_latency_follow_up(result.all_observations, instruction_id, lmul),
                    "candidate_tuples": [candidate_to_dict(candidate) for candidate in result.candidates[:32]],
                }
            )
            return record

    if non_identifiable:
        record.update(
            {
                "status": "non_identifiable",
                "value": None,
                "reason": (
                    "Current T12 consumer-gap templates are recorded by the shared simulator, "
                    "but they do not identify bypass/read-advance latency without an explicit "
                    "bypass-gap model."
                ),
                "follow_up": "Implement a T12 bypass/read-advance readiness model before claiming Latency.",
            }
        )
        return record

    if not result.candidates and direct_interval_domain_conflict(result):
        record.update(
            {
                "status": "non_identifiable",
                "value": None,
                "reason": (
                    "The real-platform stream observations are not affine under the "
                    "LLVM-facing startup+(N-1)*ReleaseAtCycles model. The profiler records "
                    "the evidence but does not claim this field without a follow-up model "
                    "for the extra platform effect."
                ),
                "follow_up": non_affine_stream_follow_up(result.all_observations),
                "conflict_examples": list(result.conflict_examples),
                "t20_startup_slope_groups": t20_startup_slope_groups(result.all_observations),
            }
        )
        return record

    if field == "ProcResource" and len(values) > 1 and result.candidates:
        first = result.all_observations[0] if result.all_observations else None
        instruction_id = first.instruction_id if first is not None else "unknown"
        lmul = first.lmul if first is not None else "unknown"
        record.update(
            {
                "status": "non_identifiable",
                "value": None,
                "reason": (
                    "T20 pair timing is recorded as startup+slope groups. Current checked-in "
                    "real traces do not provide multiple usable pair counts per pair/LMUL, so "
                    "ProcResource remains non-identifiable without overclaiming a pipe."
                ),
                "follow_up": t20_proc_resource_follow_up(result.all_observations, instruction_id, lmul),
                "t20_startup_slope_groups": t20_startup_slope_groups(result.all_observations),
                "candidate_tuples": [candidate_to_dict(candidate) for candidate in result.candidates[:32]],
            }
        )
        return record

    if not result.evidence:
        record.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "reason": "No usable marker observation constrained this field in the shared candidate simulator.",
            }
        )
    elif not result.candidates:
        record.update(
            {
                "status": "conflict",
                "value": None,
                "reason": "No candidate tuple explains all real-platform marker observations in the shared simulator.",
                "conflict_examples": list(result.conflict_examples),
            }
        )
    elif len(values) == 1:
        record.update({"status": "exact_fit", "value": values[0]})
    else:
        record.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "reason": (
                    "Multiple minimal candidate tuples explain the observations; add a focused "
                    "experiment that separates issue occupancy, pipe identity, and RAW readiness."
                ),
                "candidate_tuples": [candidate_to_dict(candidate) for candidate in result.candidates[:32]],
            }
        )
    return record


def pairwise_checks(
    items: list[RawObservation],
    release_results: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for item in items:
        if item.effective_template_id != "T20_PAIRWISE_PIPE_CLASSIFICATION":
            continue
        iterations = body_int(item, "iterations", "pair_count")
        other = item.pair_instruction_id
        detail: dict[str, Any] = {
            "experiment_id": item.experiment_id,
            "trace": item.trace_path.as_posix(),
            "other_instruction_id": other,
            "delta_cycles": item.delta_cycles,
            "iterations": iterations,
        }
        if other is None or iterations is None or iterations <= 0:
            detail["status"] = "skipped"
            detail["reason"] = "missing pair instruction or iteration count"
            checks.append(detail)
            continue
        subject_release = release_value(release_results, item.instruction_id, item.lmul)
        other_release = release_value(release_results, other, item.lmul)
        detail["cycles_per_pair"] = item.delta_cycles / iterations
        detail["subject_release"] = subject_release
        detail["other_release"] = other_release
        if subject_release is None or other_release is None:
            detail["status"] = "insufficient_evidence"
            detail["reason"] = "release candidates are required before T20 pair timing can be interpreted"
            checks.append(detail)
            continue
        pair_cycles = float(detail["cycles_per_pair"])
        if pair_cycles <= max(subject_release, other_release) and pair_cycles < subject_release + other_release:
            relation = "overlap"
        elif pair_cycles >= subject_release + other_release:
            relation = "serial"
        else:
            relation = "ambiguous"
        detail["status"] = "checked"
        detail["relation"] = relation
        detail["expected_delta_options"] = {
            "overlap": max(subject_release, other_release) * iterations,
            "serial": (subject_release + other_release) * iterations,
        }
        checks.append(detail)
    return checks


def enumerate_proc_resource(
    items: list[RawObservation],
    release_results: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    checks = pairwise_checks(items, release_results)
    labels = sorted({label for item in items for label in item.raw_pipe_labels})
    evidence = [
        evidence_entry(item, f"observed_pipe_label={label}")
        for item in items
        for label in item.raw_pipe_labels
    ]
    evidence.extend(
        f"{check['experiment_id']}:T20 relation={check.get('relation', check['status'])}"
        for check in checks
    )

    result: dict[str, Any] = {
        "field": "ProcResource",
        "candidate_domain": [proc_resource_for_label(label) for label in labels] if labels else ["unknown"],
        "evidence": evidence,
        "constraint_count": len(labels),
        "t20_relation_counts": dict(Counter(str(check.get("relation", check["status"])) for check in checks)),
    }
    if not labels:
        result.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "candidates": ["unknown"],
                "candidate_count": 1,
                "reason": (
                    "No non-synthetic trace entry carries a pipe/proc_resource label. "
                    "T20 timing checks are recorded, but they do not name a ProcResource by themselves."
                ),
            }
        )
    elif len(labels) == 1:
        value = proc_resource_for_label(labels[0])
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
                "status": "conflict",
                "value": None,
                "candidates": [proc_resource_for_label(label) for label in labels],
                "candidate_count": len(labels),
                "reason": "Raw trace entries contain multiple pipe/proc_resource labels for this instruction/LMUL.",
            }
        )
    return result, checks


def t21_expected_pair_cycles(release: int, num_micro_ops: int, single_issue: bool) -> int:
    vector_issue_cycles = max(release, num_micro_ops)
    if single_issue:
        return vector_issue_cycles + 1
    return max(vector_issue_cycles, 1)


def enumerate_issue_fields(
    items: list[RawObservation],
    release_result: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    candidate_pairs = {(num_micro_ops, single_issue) for num_micro_ops in range(1, 5) for single_issue in (False, True)}
    release = int_or_none(release_result.get("value")) if release_result.get("status") == "exact_fit" else None
    checks: list[dict[str, Any]] = []
    used = 0

    for item in items:
        if item.effective_template_id != "T21_PAIR_WITH_SCALAR":
            continue
        iterations = body_int(item, "iterations", "pair_count", "sample_count")
        check: dict[str, Any] = {
            "experiment_id": item.experiment_id,
            "trace": item.trace_path.as_posix(),
            "delta_cycles": item.delta_cycles,
            "iterations": iterations,
        }
        if release is None:
            check["status"] = "insufficient_evidence"
            check["reason"] = "ReleaseAtCycles must be uniquely identified before T21 scalar-pair timing is interpreted."
            checks.append(check)
            continue
        if iterations is None or iterations <= 0:
            check["status"] = "skipped"
            check["reason"] = "missing iteration count"
            checks.append(check)
            continue
        if item.delta_cycles % iterations != 0:
            check["status"] = "conflict"
            check["reason"] = "delta is not divisible by pair iteration count"
            candidate_pairs = set()
            checks.append(check)
            used += 1
            continue
        observed = item.delta_cycles // iterations
        valid = {
            pair
            for pair in candidate_pairs
            if t21_expected_pair_cycles(release, pair[0], pair[1]) == observed
        }
        candidate_pairs = valid
        check["status"] = "checked"
        check["cycles_per_pair"] = observed
        check["release"] = release
        check["candidate_pairs_after_check"] = [
            {"NumMicroOps": num_micro_ops, "SingleIssue": single_issue}
            for num_micro_ops, single_issue in sorted(candidate_pairs)
        ]
        checks.append(check)
        used += 1

    evidence = [
        f"{check['experiment_id']}:T21 status={check['status']}:cycles_per_pair={check.get('cycles_per_pair')}"
        for check in checks
    ]
    num_values = sorted({num_micro_ops for num_micro_ops, _single_issue in candidate_pairs})
    single_values = sorted({single_issue for _num_micro_ops, single_issue in candidate_pairs})

    num_result = discrete_field_result(
        "NumMicroOps",
        num_values,
        evidence,
        used,
        full_domain=[1, 2, 3, 4],
        empty_reason="No T21 scalar-pair marker constraint is available for NumMicroOps.",
    )
    single_result = discrete_field_result(
        "SingleIssue",
        single_values,
        evidence,
        used,
        full_domain=[False, True],
        empty_reason="No T21 scalar-pair marker constraint is available for SingleIssue.",
    )
    if release is None:
        reason = "ReleaseAtCycles is not uniquely identified, so T21 scalar-pair checks cannot distinguish issue fields."
        num_result.update({"status": "insufficient_evidence", "value": None, "reason": reason})
        single_result.update({"status": "insufficient_evidence", "value": None, "reason": reason})
    return num_result, single_result, checks


def discrete_field_result(
    field: str,
    candidates: list[Any],
    evidence: list[str],
    used_constraints: int,
    *,
    full_domain: list[Any],
    empty_reason: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "field": field,
        "candidate_domain": full_domain,
        "evidence": evidence,
        "constraint_count": used_constraints,
    }
    if used_constraints == 0:
        result.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "candidates": full_domain,
                "candidate_count": len(full_domain),
                "reason": empty_reason,
            }
        )
    elif not candidates:
        result.update(
            {
                "status": "conflict",
                "value": None,
                "candidates": [],
                "candidate_count": 0,
                "reason": "No candidate in the bounded domain satisfies all T21 checks.",
            }
        )
    elif len(candidates) == 1:
        result.update(
            {
                "status": "exact_fit",
                "value": candidates[0],
                "candidates": candidates,
                "candidate_count": 1,
            }
        )
    else:
        result.update(
            {
                "status": "insufficient_evidence",
                "value": None,
                "candidates": candidates,
                "candidate_count": len(candidates),
                "reason": "T21 checks leave multiple candidate values in the bounded domain.",
            }
        )
    return result


def fit_formula(points: dict[str, int], max_value: int) -> FormulaCandidate | None:
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


def formula_fit_for(field_results: dict[str, dict[str, Any]], max_value: int) -> dict[str, Any]:
    points = {
        lmul: int(result["value"])
        for lmul, result in field_results.items()
        if result.get("status") == "exact_fit" and int_or_none(result.get("value")) is not None
    }
    candidate = fit_formula(points, max_value)
    if candidate is None:
        return {
            "status": "insufficient_evidence",
            "form": "base_plus_lmul_times_k",
            "base": None,
            "k": None,
            "residual": None,
            "points": points,
            "reason": "At least two exact LMUL points are required for a formula fit.",
        }
    residual = int(candidate.residual) if float(candidate.residual).is_integer() else candidate.residual
    return {
        "status": "exact_fit" if candidate.residual == 0 else "approximate_fit",
        "form": "base_plus_lmul_times_k",
        "base": candidate.base,
        "k": candidate.k,
        "residual": residual,
        "points": points,
    }


def observation_summary(items: list[RawObservation]) -> dict[str, Any]:
    by_template = Counter(item.effective_template_id for item in items)
    synthetic_reference_count = sum(1 for item in items if item.synthetic_reference)
    return {
        "count": len(items),
        "by_effective_template": dict(sorted(by_template.items())),
        "synthetic_reference_count": synthetic_reference_count,
    }


def group_observations(observations: list[RawObservation]) -> dict[tuple[str, str], list[RawObservation]]:
    grouped: dict[tuple[str, str], list[RawObservation]] = defaultdict(list)
    for observation in observations:
        grouped[observation_key(observation)].append(observation)
    return dict(grouped)


def all_trace_paths(paths: list[str]) -> list[Path]:
    trace_paths: list[Path] = []
    for raw in paths:
        trace_paths.extend(trace_files_from_path(raw))
    return sorted(dict.fromkeys(trace_paths), key=lambda item: item.as_posix())


def filter_description(mode: str | None, backend: str | None, include_dry_run: bool) -> dict[str, Any]:
    return {
        "mode": mode,
        "backend": backend,
        "include_dry_run": include_dry_run,
        "dry_run_trace_excluded": not include_dry_run and (mode == "real_platform_profile" or backend == "gem5_minor"),
    }


def build_report(
    profile_paths: list[Path],
    trace_paths: list[Path],
    observations: list[RawObservation],
    configs: list[tuple[Path, dict[str, Any]]],
    warnings: list[str],
    max_value: int,
    *,
    input_counts: dict[str, int] | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    grouped = group_observations(observations)
    candidate_results = solve_candidate_sets(grouped, max_value)

    instructions: dict[str, Any] = {}
    instruction_ids = sorted({instruction_id for instruction_id, _lmul in grouped})
    for instruction_id in instruction_ids:
        lmuls = sorted({lmul for instr, lmul in grouped if instr == instruction_id}, key=lmul_sort_key)
        lmul_results: dict[str, Any] = {}
        latency_by_lmul: dict[str, dict[str, Any]] = {}
        release_by_lmul: dict[str, dict[str, Any]] = {}
        for lmul in lmuls:
            key = (instruction_id, lmul)
            items = grouped[key]
            candidate_result = candidate_results[key]
            latency = candidate_field_result("Latency", candidate_result, max_value=max_value)
            release = candidate_field_result("ReleaseAtCycles", candidate_result, max_value=max_value)
            proc_resource = candidate_field_result("ProcResource", candidate_result, max_value=max_value)
            num_micro_ops = candidate_field_result("NumMicroOps", candidate_result, max_value=max_value)
            single_issue = candidate_field_result("SingleIssue", candidate_result, max_value=max_value)
            fields = {
                "Latency": latency,
                "ReleaseAtCycles": release,
                "ProcResource": proc_resource,
                "NumMicroOps": num_micro_ops,
                "SingleIssue": single_issue,
            }
            latency_by_lmul[lmul] = latency
            release_by_lmul[lmul] = release
            lmul_results[lmul] = {
                "observation_summary": observation_summary(items),
                "fields": fields,
                "candidate_search": {
                    "candidate_count": len(candidate_result.candidates),
                    "minimal_candidate_tuples": [
                        candidate_to_dict(candidate)
                        for candidate in sorted(candidate_result.candidates, key=candidate_sort_key)[:32]
                    ],
                    "conflict_examples": list(candidate_result.conflict_examples),
                    "skipped": list(candidate_result.skipped[:32]),
                    "t20_startup_slope_groups": t20_startup_slope_groups(candidate_result.all_observations),
                },
                "template_checks": {
                    "shared_candidate_simulator": [
                        {
                            "experiment_id": item.experiment_id,
                            "template_id": item.effective_template_id,
                            "delta_cycles": item.delta_cycles,
                            "trace": item.trace_path.as_posix(),
                        }
                        for item in candidate_result.evidence
                    ],
                },
            }
        instructions[instruction_id] = {
            "lmuls": lmul_results,
            "formula_fits": {
                "Latency": formula_fit_for(latency_by_lmul, max_value),
                "ReleaseAtCycles": formula_fit_for(release_by_lmul, max_value),
            },
        }

    return {
        "schema_version": 2,
        "status": "raw_observation_parameter_search",
        "candidate_domains": {
            "Latency": f"0..{max_value}",
            "ReleaseAtCycles": f"0..{max_value}",
            "ProcResource": "observed non-synthetic pipe/proc_resource labels, otherwise unknown",
            "NumMicroOps": [1, 2, 3, 4],
            "SingleIssue": [False, True],
        },
        "global_assumptions": [
            "Only marker deltas from trace entries are used as calibration evidence.",
            "Known marker pairs are t0/t1, before/after, start/end, and begin/end; marker_baseline_cycles is subtracted.",
            "T10/T30 throughput check: marker deltas across repeated stream lengths fit startup + (N - 1) * ReleaseAtCycles.",
            "T11/T30 RAW-chain check: marker deltas constrain Latency only when body.latency_evidence, body.true_raw_chain, or body.chainable is true.",
            "T12/T30 consumer-gap checks are recorded by the shared simulator but remain non-identifiable without an explicit bypass/read-advance model.",
            "T20 pair checks are interpreted as startup+slope groups; a single usable pair count per pair/LMUL cannot identify ProcResource.",
            "T21 scalar-pair checks are evaluated inside the same candidate tuple and assume a one-cycle scalar issue companion.",
            "trace.synthetic and generated profile.yaml timing claims are reference-only and are not used as evidence.",
        ],
        "source_profiles_reference_only": [path.as_posix() for path in profile_paths],
        "source_trace_files": [path.as_posix() for path in trace_paths],
        "config_files_reference_only": [path.as_posix() for path, _data in configs],
        "filters": filters or filter_description(None, None, False),
        "input_counts": input_counts or {
            "trace_files_before_filter": len(trace_paths),
            "trace_files_after_filter": len(trace_paths),
            "usable_marker_observations": len(observations),
        },
        "observation_summary": observation_summary(observations),
        "warnings": warnings,
        "instructions": instructions,
    }


def result_status_for_field(item: dict[str, Any]) -> str:
    status = str(item.get("status", "missing"))
    if status == "exact_fit":
        return "inferred"
    if status in {"conflict", "insufficient_evidence"}:
        return status
    if status in {"missing", "unknown", "invalid", "error", "not_set"}:
        return status
    return status


def first_evidence(item: dict[str, Any], limit: int = 8) -> list[str]:
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return []
    return [str(entry) for entry in evidence[:limit]]


def field_status_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    instructions = report.get("instructions", {})
    for instruction_id in sorted(instructions):
        lmuls = instructions[instruction_id].get("lmuls", {})
        for lmul in sorted(lmuls, key=lmul_sort_key):
            fields = lmuls[lmul].get("fields", {})
            for field in FIELD_ORDER:
                item = fields.get(field, {})
                status = result_status_for_field(item)
                reason = item.get("reason")
                if not reason and status == "insufficient_evidence":
                    reason = "Current real-platform templates do not uniquely identify this LLVM-facing field."
                elif not reason and status == "conflict":
                    reason = "No bounded candidate explains all real-platform marker observations for this field."
                elif not reason and status == "inferred":
                    reason = "Unique candidate inferred from real-platform marker observations."
                follow_up = item.get("follow_up")
                if not follow_up and status in {"conflict", "insufficient_evidence", "non_identifiable", "missing", "unknown"}:
                    if field == "Latency":
                        follow_up = t12_latency_follow_up((), instruction_id, lmul)
                    elif field == "ProcResource":
                        follow_up = t20_proc_resource_follow_up((), instruction_id, lmul)
                    else:
                        follow_up = (
                            f"Add focused template coverage for instruction={instruction_id} "
                            f"lmul={lmul} field={field}; keep register policy explicit in metadata."
                        )
                row = {
                    "instruction_id": instruction_id,
                    "lmul": lmul,
                    "field": field,
                    "status": status,
                    "source_status": item.get("status", "missing"),
                    "candidate": item.get("value"),
                    "candidates": item.get("candidates", []),
                    "candidate_count": item.get("candidate_count"),
                    "constraint_count": item.get("constraint_count", 0),
                    "reason": reason,
                    "follow_up": follow_up,
                    "evidence": first_evidence(item),
                }
                rows.append(row)
    return rows


def build_field_status(report: dict[str, Any]) -> dict[str, Any]:
    rows = field_status_rows(report)
    status_counts = Counter(str(row.get("status", "missing")) for row in rows)
    blocking_statuses = {"conflict", "insufficient_evidence", "missing", "unknown", "invalid", "error", "not_set"}
    blocking_counts = {
        status: count for status, count in sorted(status_counts.items()) if status in blocking_statuses
    }
    # The full trace list is already recorded in the search report; keep this
    # sidecar compact and hash the report inputs by path for approval binding.
    artifact_hash_inputs = [
        {"path": path, "sha256": file_sha256(Path(path))}
        for path in report.get("source_trace_files", [])
        if Path(path).exists()
    ]
    return {
        "schema_version": 1,
        "mode": report.get("filters", {}).get("mode"),
        "backend": report.get("filters", {}).get("backend"),
        "filters": report.get("filters", {}),
        "input_counts": report.get("input_counts", {}),
        "required_fields": list(FIELD_ORDER),
        "artifact_hash_inputs": artifact_hash_inputs,
        "summary": {
            "total_rows": len(rows),
            "required_fields": list(FIELD_ORDER),
            "status_counts": dict(sorted(status_counts.items())),
            "blocking_status_counts": blocking_counts,
            "blocking_total": sum(blocking_counts.values()),
        },
        "rows": rows,
    }


def profile_for_instruction(instruction_id: str, rows: list[dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    by_lmul: dict[str, dict[str, Any]] = defaultdict(dict)
    for row in rows:
        if row["instruction_id"] != instruction_id:
            continue
        by_lmul[row["lmul"]][row["field"]] = {
            "status": row["status"],
            "value": row["candidate"],
            "candidates": row["candidates"],
            "reason": row["reason"],
            "evidence": row["evidence"],
        }
    return {
        "schema_version": 1,
        "mode": "real_platform_profile",
        "backend": report.get("filters", {}).get("backend"),
        "instruction_id": instruction_id,
        "llvm_facing_fields": dict(sorted(by_lmul.items(), key=lambda item: lmul_sort_key(item[0]))),
        "hardware_interpretation": {
            "issue_width": 2,
            "issue_order": "in_order",
            "rob": "none",
            "vector_pipes": 2,
            "timestamp_marker_cost": 0,
        },
        "confidence": {
            "source": "mode_isolated_real_platform_marker_observations",
            "blocking_statuses": ["conflict", "insufficient_evidence", "missing", "unknown"],
        },
    }


def common_output_root(profile_args: list[str], output: str | None) -> Path:
    candidates = [Path(raw) for raw in profile_args]
    if output:
        candidates.append(Path(output))
    for path in candidates:
        current = path if path.is_dir() else path.parent
        for ancestor in (current, *current.parents):
            if ancestor.name == "common":
                return ancestor
            if (ancestor / "common").exists():
                return ancestor / "common"
    return Path("results/common")


def write_real_platform_artifacts(report: dict[str, Any], common_root: Path) -> None:
    common_root.mkdir(parents=True, exist_ok=True)
    field_status = build_field_status(report)
    field_status_path = common_root / "real_platform_field_status.json"
    field_status_path.write_text(json.dumps(field_status, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows = field_status["rows"]
    result_root = common_root.parent if common_root.name == "common" else common_root
    for instruction_id in sorted({row["instruction_id"] for row in rows}):
        profile = profile_for_instruction(instruction_id, rows, report)
        instr_dir = result_root / instruction_id
        instr_dir.mkdir(parents=True, exist_ok=True)
        (instr_dir / "profile.real_platform.yaml").write_text(dump_yaml(profile) + "\n", encoding="utf-8")


def value_text(item: dict[str, Any]) -> str:
    if item.get("status") == "exact_fit":
        return str(item.get("value"))
    candidates = item.get("candidates")
    if isinstance(candidates, list) and 0 < len(candidates) <= 6:
        return ", ".join(str(candidate) for candidate in candidates)
    if isinstance(candidates, list) and len(candidates) > 6:
        return f"{len(candidates)} candidates"
    return "n/a"


def render_markdown(report: dict[str, Any]) -> str:
    input_counts = report.get("input_counts", {})
    filters = report.get("filters", {})
    lines = [
        "# Timing Parameter Search",
        "",
        f"Status: {report['status']}",
        "",
        "## Inputs",
        "",
        f"- trace files before filter: {input_counts.get('trace_files_before_filter', len(report.get('source_trace_files', [])))}",
        f"- trace files after filter: {input_counts.get('trace_files_after_filter', len(report.get('source_trace_files', [])))}",
        f"- usable marker observations: {report.get('observation_summary', {}).get('count', 0)}",
        f"- profile summaries reference-only: {len(report.get('source_profiles_reference_only', []))}",
        f"- mode filter: `{filters.get('mode')}`",
        f"- backend filter: `{filters.get('backend')}`",
        "",
        "## Global Assumptions",
        "",
    ]
    for assumption in report.get("global_assumptions", []):
        lines.append(f"- {assumption}")

    warnings = report.get("warnings") or []
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings[:20]:
            lines.append(f"- {warning}")
        if len(warnings) > 20:
            lines.append(f"- ... {len(warnings) - 20} more warnings")

    lines.extend(
        [
            "",
            "## Candidates",
            "",
            "| Instruction | LMUL | Field | Status | Candidate | Evidence |",
            "| --- | --- | --- | --- | --- | ---: |",
        ]
    )
    instructions = report.get("instructions", {})
    if not instructions:
        lines.append("| n/a | n/a | n/a | insufficient_evidence | n/a | 0 |")
    for instruction_id in sorted(instructions):
        lmuls = instructions[instruction_id].get("lmuls", {})
        for lmul in sorted(lmuls, key=lmul_sort_key):
            fields = lmuls[lmul].get("fields", {})
            for field in FIELD_ORDER:
                item = fields.get(field, {})
                lines.append(
                    f"| `{instruction_id}` | `{lmul}` | `{field}` | "
                    f"{item.get('status', 'missing')} | `{value_text(item)}` | "
                    f"{item.get('constraint_count', 0)} |"
                )

    lines.extend(["", "## Formula Fits", ""])
    lines.append("| Instruction | Field | Status | Formula | Residual |")
    lines.append("| --- | --- | --- | --- | ---: |")
    for instruction_id in sorted(instructions):
        fits = instructions[instruction_id].get("formula_fits", {})
        for field in ("Latency", "ReleaseAtCycles"):
            fit = fits.get(field, {})
            if fit.get("base") is not None and fit.get("k") is not None:
                formula = f"{fit['base']} + {fit['k']} * LMUL"
            else:
                formula = "n/a"
            residual = fit.get("residual")
            lines.append(
                f"| `{instruction_id}` | `{field}` | {fit.get('status', 'missing')} | "
                f"`{formula}` | {residual if residual is not None else 'n/a'} |"
            )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search conservative RVV timing-model candidates.")
    parser.add_argument("--config", action="append", default=[], help="YAML-ish timing config file or directory.")
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Results root, profile.yaml, trace.json, or directory containing trace.json files.",
    )
    parser.add_argument("--output", help="Optional output path.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--max-value", type=int, default=128, help="Maximum integer candidate value to enumerate.")
    parser.add_argument("--mode", help="Optional trace JSON mode filter, e.g. real_platform_profile.")
    parser.add_argument("--backend", help="Optional trace JSON backend filter, e.g. gem5_minor.")
    parser.add_argument(
        "--include-dry-run",
        action="store_true",
        help="Include dry_run_trace entries even when selecting real-platform/gem5 traces.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_paths = load_profiles(args.profile)
    configs = load_configs(args.config)
    before_filter = all_trace_paths(args.profile)
    observations, trace_paths, warnings = load_observations(
        args.profile,
        mode=args.mode,
        backend=args.backend,
        include_dry_run=args.include_dry_run,
    )
    filters = filter_description(args.mode, args.backend, args.include_dry_run)
    input_counts = {
        "trace_files_before_filter": len(before_filter),
        "trace_files_after_filter": len(trace_paths),
        "usable_marker_observations": len(observations),
    }
    report = build_report(
        profile_paths,
        trace_paths,
        observations,
        configs,
        warnings,
        args.max_value,
        input_counts=input_counts,
        filters=filters,
    )
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

    real_platform_selected = args.mode == "real_platform_profile" or args.backend == "gem5_minor"
    if real_platform_selected:
        common_root = common_output_root(args.profile, args.output)
        write_real_platform_artifacts(report, common_root)
        summary_path = common_root / "search_model_real_platform_summary.md"
        summary_path.write_text(render_markdown(report), encoding="utf-8")
        json_path = common_root / "search_model_real_platform.json"
        if Path(args.output or "") != json_path:
            json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
