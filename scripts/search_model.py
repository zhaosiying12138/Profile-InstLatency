#!/usr/bin/env python3
"""Search conservative RVV timing parameters from raw trace observations.

The search consumes ``trace.json`` files under ``results/**/experiments/**``
plus their sibling ``experiment.yaml`` metadata.  Marker deltas are used as the
only calibration evidence.  Synthetic golden timing fields may be carried
through as labeled references, but they are never used to claim a candidate.
"""

from __future__ import annotations

import argparse
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
PIPE_RESOURCE = {
    "any": "YuShuXinAnyVPipe",
    "pipe0": "YuShuXinVPipe0",
    "pipe1": "YuShuXinVPipe1",
}
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


def load_trace_observations(trace_path: Path) -> tuple[list[RawObservation], list[str]]:
    warnings: list[str] = []
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
            )
        )
    return observations, warnings


def load_observations(paths: list[str]) -> tuple[list[RawObservation], list[Path], list[str]]:
    trace_paths: list[Path] = []
    for raw in paths:
        trace_paths.extend(trace_files_from_path(raw))
    trace_paths = sorted(dict.fromkeys(trace_paths), key=lambda item: item.as_posix())

    observations: list[RawObservation] = []
    warnings: list[str] = []
    for trace_path in trace_paths:
        loaded, trace_warnings = load_trace_observations(trace_path)
        observations.extend(loaded)
        warnings.extend(trace_warnings)
    return observations, trace_paths, warnings


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
            if iterations is None or iterations <= 0:
                skipped.append(evidence_entry(item, "T11 skipped:missing_iterations"))
                continue
            candidates &= {value for value in candidates if item.delta_cycles == iterations * value}
            used.append(evidence_entry(item, f"T11 expected delta=iterations*Latency;iterations={iterations}"))
        elif shape == "T12_CONSUMER_RAW_GAP":
            filler_count = body_int(item, "filler_count")
            if filler_count is None:
                skipped.append(evidence_entry(item, "T12 skipped:missing_filler_count"))
                continue
            candidates &= {value for value in candidates if item.delta_cycles == filler_count + value}
            used.append(evidence_entry(item, f"T12 expected delta=filler_count+Latency;filler_count={filler_count}"))

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
        if iterations is None or iterations <= 0:
            skipped.append(evidence_entry(item, "T10 skipped:missing_iterations"))
            continue
        candidates &= {value for value in candidates if item.delta_cycles == iterations * value}
        used.append(evidence_entry(item, f"T10 expected delta=iterations*ReleaseAtCycles;iterations={iterations}"))

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
        if item.delta_cycles % iterations != 0:
            detail["status"] = "conflict"
            detail["reason"] = "delta is not divisible by pair iteration count"
            checks.append(detail)
            continue
        subject_release = release_value(release_results, item.instruction_id, item.lmul)
        other_release = release_value(release_results, other, item.lmul)
        detail["cycles_per_pair"] = item.delta_cycles // iterations
        detail["subject_release"] = subject_release
        detail["other_release"] = other_release
        if subject_release is None or other_release is None:
            detail["status"] = "insufficient_evidence"
            detail["reason"] = "release candidates are required before T20 pair timing can be interpreted"
            checks.append(detail)
            continue
        pair_cycles = int(detail["cycles_per_pair"])
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


def build_report(
    profile_paths: list[Path],
    trace_paths: list[Path],
    observations: list[RawObservation],
    configs: list[tuple[Path, dict[str, Any]]],
    warnings: list[str],
    max_value: int,
) -> dict[str, Any]:
    grouped = group_observations(observations)
    latency_results: dict[tuple[str, str], dict[str, Any]] = {}
    release_results: dict[tuple[str, str], dict[str, Any]] = {}
    for key, items in grouped.items():
        latency_results[key] = enumerate_latency(items, max_value)
        release_results[key] = enumerate_release(items, max_value)

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
            proc_resource, t20_checks = enumerate_proc_resource(items, release_results)
            num_micro_ops, single_issue, t21_checks = enumerate_issue_fields(items, release_results[key])
            fields = {
                "Latency": latency_results[key],
                "ReleaseAtCycles": release_results[key],
                "ProcResource": proc_resource,
                "NumMicroOps": num_micro_ops,
                "SingleIssue": single_issue,
            }
            latency_by_lmul[lmul] = latency_results[key]
            release_by_lmul[lmul] = release_results[key]
            lmul_results[lmul] = {
                "observation_summary": observation_summary(items),
                "fields": fields,
                "template_checks": {
                    "T20_PAIRWISE_PIPE_CLASSIFICATION": t20_checks,
                    "T21_PAIR_WITH_SCALAR": t21_checks,
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
            "T10/T30 throughput check: delta_cycles == iterations * ReleaseAtCycles.",
            "T11/T30 RAW-chain check: delta_cycles == iterations * Latency.",
            "T12/T30 consumer-gap check: delta_cycles == filler_count + Latency.",
            "T20 pair checks compare pair cycles with already identified per-instruction ReleaseAtCycles.",
            "T21 scalar-pair checks assume a one-cycle scalar issue companion; ambiguous NumMicroOps/SingleIssue cases stay insufficient_evidence.",
            "trace.synthetic and generated profile.yaml timing claims are reference-only and are not used as evidence.",
        ],
        "source_profiles_reference_only": [path.as_posix() for path in profile_paths],
        "source_trace_files": [path.as_posix() for path in trace_paths],
        "config_files_reference_only": [path.as_posix() for path, _data in configs],
        "observation_summary": observation_summary(observations),
        "warnings": warnings,
        "instructions": instructions,
    }


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
    lines = [
        "# Timing Parameter Search",
        "",
        f"Status: {report['status']}",
        "",
        "## Inputs",
        "",
        f"- trace files: {len(report.get('source_trace_files', []))}",
        f"- usable marker observations: {report.get('observation_summary', {}).get('count', 0)}",
        f"- profile summaries reference-only: {len(report.get('source_profiles_reference_only', []))}",
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile_paths = load_profiles(args.profile)
    configs = load_configs(args.config)
    observations, trace_paths, warnings = load_observations(args.profile)
    report = build_report(profile_paths, trace_paths, observations, configs, warnings, args.max_value)
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
