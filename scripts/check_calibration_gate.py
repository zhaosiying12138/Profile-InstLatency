#!/usr/bin/env python3
"""Check whether profiling results are ready to advance.

Synthetic calibration is a non-circular check: generated ``profile.yaml``
claims must be sourced from raw marker evidence before they are compared with
``config/rvv_timing_model.yaml``.  Real-platform profiling is deliberately
different: it depends on coverage, stability, confidence, assumptions,
conflict resolution, and explicit human approval, not synthetic golden
equality.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


LMUL_ORDER = ("m1", "m2", "m4")
LMUL_VALUE = {"m1": 1, "m2": 2, "m4": 4, "m8": 8}
PIPE_RESOURCE = {
    "any": "YuShuXinAnyVPipe",
    "pipe0": "YuShuXinVPipe0",
    "pipe1": "YuShuXinVPipe1",
}

REQUIRED_REAL_TEMPLATES = (
    "T00_BASELINE_MARKER",
    "T01_DECODE_EXEC_KILLCHECK",
    "T10_INDEPENDENT_STREAM_THROUGHPUT",
    "T11_SELF_RAW_CHAIN",
    "T12_CONSUMER_RAW_GAP",
    "T20_PAIRWISE_PIPE_CLASSIFICATION",
    "T21_PAIR_WITH_SCALAR",
    "T30_LMUL_SCALING",
)
DEFERRED_REAL_TEMPLATES = ("T40_COMMON_VLSU_LOAD_HIT",)
UNKNOWN_CONFIDENCE_VALUES = {
    "",
    "unknown",
    "none",
    "null",
    "not_set",
    "tbd",
    "todo",
    "insufficient",
    "insufficient_raw_marker_evidence",
    "not_identifiable",
    "conflict",
}
PASS_APPROVAL_VALUES = ("approved", "granted", "yes", "true", "pass")
BLOCKING_FIELD_STATUSES = {
    "conflict",
    "insufficient_evidence",
    "non_identifiable",
    "missing",
    "unknown",
    "invalid",
    "error",
    "not_set",
}
ALL_RISKS_ACCEPTANCE_VALUES = {
    "*",
    "all",
    "all_risks",
    "all_unresolved",
    "all_unresolved_risks",
    "all_field_status_risks",
    "all_real_platform_field_status_risks",
}


@dataclass(frozen=True)
class ExpectedExperiment:
    experiment_id: str
    template_id: str
    result_group: str
    path: Path


@dataclass(frozen=True)
class TraceObservation:
    experiment_id: str
    template_id: str
    result_group: str
    mode: str
    backend: str
    dry_run: bool
    gem5_returncode: int | None
    entries_count: int
    identity: str


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


def nested_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


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


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    return bool(value)


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing required report: {path}")
    return path.read_text(encoding="utf-8")


def has_pass_status(text: str) -> bool:
    return any(line.strip().lower() == "gate status: pass" for line in text.splitlines())


def profile_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("*/profile.yaml"), key=lambda path: path.as_posix())


def load_profiles(root: Path) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for path in profile_paths(root):
        profile = parse_yamlish(path)
        instr = nested_get(profile, ("instruction", "id"))
        if instr:
            profiles[str(instr)] = profile
    return profiles


def expected_value(config_instr: dict[str, Any], field: str, lmul: str) -> int | None:
    base = int_or_none(config_instr.get(f"{field}_base"))
    k = int_or_none(config_instr.get(f"{field}_lmul_k"))
    factor = LMUL_VALUE.get(lmul)
    if base is None or k is None or factor is None:
        return None
    return base + k * factor


def resource_for_pipe(pipe: Any) -> str | None:
    if pipe is None:
        return None
    return PIPE_RESOURCE.get(str(pipe), str(pipe))


def record_provenance_failures(record: Any, label: str) -> list[str]:
    if not isinstance(record, dict) or not record.get("claimed"):
        return [f"{label}: not claimed"]
    lowered_confidence = str(record.get("confidence", "")).lower()
    lowered_source = str(record.get("source", "")).lower()
    if "synthetic" in lowered_confidence or "synthetic" in lowered_source:
        return [f"{label}: sourced from synthetic metadata ({record.get('confidence')}/{record.get('source')})"]
    if lowered_source == "raw_marker_observation":
        return []
    evidence = record.get("evidence")
    if isinstance(evidence, list) and any("raw_marker_delta" in str(item) for item in evidence):
        return []
    return [f"{label}: missing non-circular raw marker evidence"]


def synthetic_profile_failures(profile_root: Path, config_path: Path) -> list[str]:
    failures: list[str] = []
    if not config_path.exists():
        return [f"missing timing config: {config_path}"]
    timing_config = parse_yamlish(config_path)
    instructions = timing_config.get("instructions")
    if not isinstance(instructions, dict):
        return ["timing config has no instructions map"]
    profiles = load_profiles(profile_root)
    if not profiles:
        return [f"no profile.yaml files found under {profile_root}"]

    for instr_id, raw_config in instructions.items():
        config_instr = raw_config if isinstance(raw_config, dict) else {}
        profile = profiles.get(instr_id)
        if profile is None:
            failures.append(f"{instr_id}: missing profile.yaml")
            continue
        mode = profile.get("mode")
        if mode != "synthetic_calibration":
            failures.append(f"{instr_id}: profile mode is {mode}, expected synthetic_calibration")
        asm = nested_get(profile, ("instruction", "asm"))
        if asm != config_instr.get("asm"):
            failures.append(f"{instr_id}: asm profile={asm} config={config_instr.get('asm')}")

        measurements = profile.get("measurements")
        if not isinstance(measurements, dict):
            failures.append(f"{instr_id}: profile has no measurements")
            continue
        expected_pipe = config_instr.get("pipe")
        expected_resource = resource_for_pipe(expected_pipe)
        for lmul in LMUL_ORDER:
            lmul_measurement = measurements.get(lmul)
            if not isinstance(lmul_measurement, dict):
                failures.append(f"{instr_id}.{lmul}: missing measurement")
                continue
            for profile_field, config_field in (("latency", "latency"), ("release_at_cycles", "release")):
                record = nested_get(lmul_measurement, ("llvm", profile_field))
                provenance_failures = record_provenance_failures(record, f"{instr_id}.{lmul}.{profile_field}")
                if provenance_failures:
                    failures.extend(provenance_failures)
                    continue
                value = int_or_none(record.get("value"))
                expected = expected_value(config_instr, config_field, lmul)
                if value != expected:
                    failures.append(f"{instr_id}.{lmul}.{profile_field}: profile={value} config={expected}")
            pipe_record = nested_get(lmul_measurement, ("llvm", "pipe_affinity"))
            provenance_failures = record_provenance_failures(pipe_record, f"{instr_id}.{lmul}.pipe_affinity")
            if provenance_failures:
                failures.extend(provenance_failures)
            elif pipe_record.get("value") != expected_pipe:
                failures.append(
                    f"{instr_id}.{lmul}.pipe_affinity: profile={pipe_record.get('value')} config={expected_pipe}"
                )
            resource_record = nested_get(lmul_measurement, ("llvm", "resource_group"))
            provenance_failures = record_provenance_failures(resource_record, f"{instr_id}.{lmul}.resource_group")
            if provenance_failures:
                failures.extend(provenance_failures)
            elif resource_record.get("value") != expected_resource:
                failures.append(
                    f"{instr_id}.{lmul}.resource_group: profile={resource_record.get('value')} config={expected_resource}"
                )

        fit = profile.get("fit")
        if not isinstance(fit, dict):
            failures.append(f"{instr_id}: missing fit section")
            continue
        for fit_key, config_field in (("latency_formula", "latency"), ("release_formula", "release")):
            record = fit.get(fit_key)
            provenance_failures = record_provenance_failures(record, f"{instr_id}.{fit_key}")
            if provenance_failures:
                failures.extend(provenance_failures)
                continue
            base = int_or_none(record.get("base"))
            k = int_or_none(record.get("k"))
            expected_base = int_or_none(config_instr.get(f"{config_field}_base"))
            expected_k = int_or_none(config_instr.get(f"{config_field}_lmul_k"))
            residual = int_or_none(record.get("residual"))
            if base != expected_base or k != expected_k or residual != 0:
                failures.append(
                    f"{instr_id}.{fit_key}: profile={base}+{k}*LMUL residual={residual} "
                    f"config={expected_base}+{expected_k}*LMUL"
                )
    return failures


def synthetic_report_failures(text: str) -> list[str]:
    lowered = text.lower()
    failures: list[str] = []
    if "mode: synthetic_calibration" not in lowered:
        failures.append("mismatch report must declare `mode: synthetic_calibration`")
    if "inference source status: non_circular_raw_marker_evidence" not in lowered:
        failures.append("mismatch report must declare non-circular raw marker inference source status")
    if not has_pass_status(text):
        failures.append("mismatch report must contain exact line `Gate status: PASS`")
    claimed_line = next((line for line in text.splitlines() if line.lower().startswith("claimed mismatches:")), "")
    if not claimed_line:
        failures.append("mismatch report must contain `Claimed mismatches: none` or `0`")
    else:
        value = claimed_line.split(":", 1)[1].strip().lower()
        if value not in ("none", "0", "zero"):
            failures.append(f"claimed mismatches are not clear-none: {claimed_line}")
    conflict_markers = ("confidence: conflict", "synthetic.golden.mismatch", "status: mismatch")
    for marker in conflict_markers:
        if marker in lowered:
            failures.append(f"mismatch report still contains conflict marker `{marker}`")
    return failures


def synthetic_failures(text: str, profile_root: Path, config_path: Path) -> list[str]:
    return synthetic_report_failures(text) + synthetic_profile_failures(profile_root, config_path)


def common_result_root(profile_root: Path) -> Path:
    if profile_root.name == "common":
        return profile_root
    candidate = profile_root / "common"
    if candidate.exists():
        return candidate
    return profile_root


def selected_result_groups(profile_root: Path) -> set[str]:
    groups: set[str] = set()
    if (profile_root / "experiments").exists():
        groups.add(profile_root.name)
    if profile_root.exists():
        for child in profile_root.iterdir():
            if child.is_dir() and (child / "experiments").exists():
                groups.add(child.name)
    return groups


def load_expected_experiments(profile_root: Path) -> tuple[list[ExpectedExperiment], list[ExpectedExperiment]]:
    selected_groups = selected_result_groups(profile_root)
    required: list[ExpectedExperiment] = []
    deferred: list[ExpectedExperiment] = []
    for path in sorted(Path("experiments/generated").glob("*/experiment.yaml"), key=lambda item: item.as_posix()):
        data = parse_yamlish(path)
        experiment_id = data.get("experiment_id")
        template_id = data.get("template_id")
        result_group = data.get("result_group")
        if not experiment_id or not template_id or not result_group:
            continue
        if selected_groups and str(result_group) not in selected_groups:
            continue
        expected = ExpectedExperiment(str(experiment_id), str(template_id), str(result_group), path)
        if expected.template_id in REQUIRED_REAL_TEMPLATES:
            required.append(expected)
        elif expected.template_id in DEFERRED_REAL_TEMPLATES:
            deferred.append(expected)
    return required, deferred


def infer_result_group(path: Path, profile_root: Path) -> str:
    try:
        relative = path.relative_to(profile_root)
    except ValueError:
        return ""
    parts = relative.parts
    if len(parts) >= 3 and parts[1] == "experiments":
        return parts[0]
    if "experiments" in parts:
        index = parts.index("experiments")
        if index > 0:
            return parts[index - 1]
    return ""


def trace_observation_from_data(data: dict[str, Any], identity: str, profile_root: Path) -> TraceObservation | None:
    experiment_id = data.get("experiment_id") or Path(identity).parent.name
    template_id = data.get("template_id")
    if not experiment_id or not template_id:
        return None
    result_group = data.get("result_group")
    if not result_group:
        result_group = infer_result_group(Path(identity), profile_root)
    entries = data.get("entries")
    explicit_entries_count = int_or_none(data.get("entries_count", data.get("entry_count")))
    gem5 = data.get("gem5")
    gem5_returncode = int_or_none(gem5.get("returncode")) if isinstance(gem5, dict) else None
    return TraceObservation(
        experiment_id=str(experiment_id),
        template_id=str(template_id),
        result_group=str(result_group or ""),
        mode=str(data.get("mode", "")),
        backend=str(data.get("backend", "")),
        dry_run=bool_value(data.get("dry_run_trace", False)),
        gem5_returncode=gem5_returncode,
        entries_count=len(entries) if isinstance(entries, list) else explicit_entries_count or 0,
        identity=identity,
    )


def load_trace_observations(profile_root: Path) -> tuple[list[TraceObservation], list[str]]:
    observations: list[TraceObservation] = []
    failures: list[str] = []
    if not profile_root.exists():
        return observations, [f"profile root does not exist: {profile_root}"]
    for path in sorted(profile_root.glob("**/trace.json"), key=lambda item: item.as_posix()):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            failures.append(f"{path}: invalid trace JSON: {error}")
            continue
        if not isinstance(data, dict):
            failures.append(f"{path}: trace JSON root is not an object")
            continue
        observation = trace_observation_from_data(data, path.as_posix(), profile_root)
        if observation is not None:
            observations.append(observation)
    return observations, failures


def find_inventory_path(profile_root: Path) -> Path:
    return common_result_root(profile_root) / "real_platform_inventory.json"


def load_inventory(profile_root: Path) -> tuple[Path, dict[str, Any] | None, list[str]]:
    path = find_inventory_path(profile_root)
    if not path.exists():
        return path, None, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return path, None, [f"{path}: invalid real-platform inventory JSON: {error}"]
    if not isinstance(data, dict):
        return path, None, [f"{path}: inventory JSON root is not an object"]
    return path, data, []


def walk_dicts(data: Any, prefix: str = "$") -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(data, dict):
        found.append((prefix, data))
        for key, value in data.items():
            found.extend(walk_dicts(value, f"{prefix}.{key}"))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            found.extend(walk_dicts(value, f"{prefix}[{index}]"))
    return found


def inventory_observations(inventory: dict[str, Any] | None, profile_root: Path) -> list[TraceObservation]:
    if not inventory:
        return []
    observations: list[TraceObservation] = []
    for index, (_, item) in enumerate(walk_dicts(inventory)):
        experiment_id = item.get("experiment_id") or item.get("id")
        template_id = item.get("template_id")
        if not experiment_id or not template_id:
            continue
        trace_path = item.get("trace_path") or item.get("path")
        identity = str(trace_path) if trace_path else f"inventory:{index}:{experiment_id}"
        observation = trace_observation_from_data(
            {
                "experiment_id": experiment_id,
                "template_id": template_id,
                "result_group": item.get("result_group"),
                "mode": item.get("mode"),
                "backend": item.get("backend"),
                "dry_run_trace": item.get("dry_run_trace", item.get("dry_run", False)),
                "entries_count": item.get("entries_count", item.get("entry_count")),
                "entries": item.get("entries", [None] if item.get("has_entries") else []),
                "gem5": item.get("gem5", {"returncode": item.get("gem5_returncode")}),
            },
            identity,
            profile_root,
        )
        if observation is not None:
            observations.append(observation)
    return observations


def is_real_gem5_observation(observation: TraceObservation) -> bool:
    backend = observation.backend.lower()
    return (
        observation.mode == "real_platform_profile"
        and not observation.dry_run
        and ("gem5" in backend or observation.gem5_returncode is not None)
        and observation.gem5_returncode in (None, 0)
        and observation.entries_count > 0
    )


def real_observation_counts(observations: list[TraceObservation]) -> dict[str, int]:
    by_experiment: dict[str, set[str]] = {}
    for observation in observations:
        if not is_real_gem5_observation(observation):
            continue
        by_experiment.setdefault(observation.experiment_id, set()).add(observation.identity)
    return {experiment_id: len(identities) for experiment_id, identities in by_experiment.items()}


def summarize_expected_missing(label: str, expected: list[ExpectedExperiment], missing: list[ExpectedExperiment]) -> list[str]:
    if not missing:
        return []
    failures = [f"{label}: {len(missing)}/{len(expected)} required experiment groups are missing"]
    for template_id in REQUIRED_REAL_TEMPLATES:
        examples = [item.experiment_id for item in missing if item.template_id == template_id]
        if not examples:
            continue
        suffix = ", ".join(examples[:5])
        if len(examples) > 5:
            suffix += f", ... (+{len(examples) - 5} more)"
        failures.append(f"{label}: {template_id} missing {len(examples)}; examples: {suffix}")
    return failures


def truthy_status(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    lowered = str(value).strip().lower()
    return lowered in PASS_APPROVAL_VALUES or lowered.startswith("approved ") or lowered.startswith("granted ")


def truthy_waiver_status(value: Any) -> bool:
    if truthy_status(value):
        return True
    lowered = str(value).strip().lower() if value is not None else ""
    return lowered in ("waived", "accepted")


def canonical_key(key: Any) -> str:
    return str(key).strip().lstrip("-").strip()


def canonical_json_key(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


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


def is_blocking_field_status(value: Any) -> bool:
    return normalize_field_status(value) in BLOCKING_FIELD_STATUSES


def get_any(data: dict[str, Any], names: set[str]) -> Any:
    for key, value in data.items():
        if canonical_key(key) in names:
            return value
    return None


def find_values_by_key(data: Any, names: set[str]) -> list[Any]:
    values: list[Any] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if canonical_key(key) in names:
                values.append(value)
            values.extend(find_values_by_key(value, names))
    elif isinstance(data, list):
        for value in data:
            values.extend(find_values_by_key(value, names))
    return values


def top_level_values_by_key(data: Any, names: set[str]) -> list[Any]:
    if not isinstance(data, dict):
        return []
    return [value for key, value in data.items() if canonical_json_key(key) in names]


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
        risk_id = get_any(value, {"risk_id", "id"})
        if risk_id is not None and str(risk_id).strip():
            risk_ids.add(str(risk_id).strip())
        for nested in value.values():
            if isinstance(nested, (dict, list)):
                risk_ids.update(risk_ids_from_value(nested))
    return risk_ids


def accepted_risk_ids_from_document(data: dict[str, Any] | None) -> set[str]:
    if not isinstance(data, dict):
        return set()
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


def field_status_blocking_count(field_status: dict[str, Any]) -> int:
    counts = field_status.get("status_counts")
    if not isinstance(counts, dict):
        return 0
    total = 0
    for status, count in counts.items():
        if not is_blocking_field_status(status):
            continue
        parsed = int_or_none(count)
        if parsed is not None:
            total += parsed
    return total


def field_status_unresolved_records(field_status: dict[str, Any]) -> list[dict[str, Any]]:
    unresolved = field_status.get("unresolved")
    if isinstance(unresolved, list) and unresolved:
        return [record for record in unresolved if isinstance(record, dict)]
    rows = field_status.get("rows")
    if isinstance(rows, list):
        return [
            record
            for record in rows
            if isinstance(record, dict) and is_blocking_field_status(record.get("status"))
        ]
    count_only_records: list[dict[str, Any]] = []
    counts = field_status.get("status_counts")
    if isinstance(counts, dict):
        for status, count in counts.items():
            if not is_blocking_field_status(status):
                continue
            parsed = int_or_none(count) or 0
            if parsed:
                count_only_records.append(
                    {
                        "risk_id": f"real_platform_field_status:{normalize_field_status(status)}",
                        "status": normalize_field_status(status),
                        "reason": f"status_counts reports {parsed} blocking field-status rows.",
                    }
                )
    return count_only_records


def field_status_risks_accepted(field_status: dict[str, Any], approval: dict[str, Any] | None) -> bool:
    unresolved_records = field_status_unresolved_records(field_status)
    unresolved_total = max(
        int_or_none(field_status.get("unresolved_total")) or 0,
        len(unresolved_records),
        field_status_blocking_count(field_status),
    )
    if unresolved_total == 0:
        return True
    accepted = accepted_risk_ids_from_document(approval)
    accepted_lower = {risk_id.lower() for risk_id in accepted}
    if accepted_lower & ALL_RISKS_ACCEPTANCE_VALUES:
        return True
    required = {
        str(record.get("risk_id")).strip()
        for record in unresolved_records
        if isinstance(record, dict) and str(record.get("risk_id", "")).strip()
    }
    return bool(required) and required <= accepted


def approval_file(profile_root: Path) -> Path | None:
    root = common_result_root(profile_root)
    for name in ("human_approval.json", "human_approval.yaml", "human_approval.yml"):
        path = root / name
        if path.exists():
            return path
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_approval(profile_root: Path) -> tuple[Path | None, dict[str, Any] | None, list[str]]:
    path = approval_file(profile_root)
    if path is None:
        return None, None, []
    try:
        data = parse_yamlish(path)
    except (OSError, json.JSONDecodeError) as error:
        return path, None, [f"{path}: invalid human approval file: {error}"]
    return path, data, []


def human_approval_failures(
    profile_root: Path,
    inventory_path: Path,
    inventory: dict[str, Any] | None,
    total_traces: int,
    real_traces: int,
) -> tuple[bool, list[str], dict[str, Any] | None]:
    path, approval, failures = load_approval(profile_root)
    if path is None:
        return False, [f"missing machine-readable human approval file under {common_result_root(profile_root)}"] + failures, None
    if approval is None:
        return False, failures, None

    status_values = top_level_values_by_key(
        approval, {"approved", "status", "approval_status", "human_approval"}
    )
    approved = bool(status_values) and all(truthy_status(value) for value in status_values)
    if not approved:
        failures.append(f"{path}: approval status is not approved/granted/pass")

    approver_values = find_values_by_key(approval, {"approved_by", "approver", "reviewer", "human"})
    if not any(str(value).strip() for value in approver_values if value is not None):
        failures.append(f"{path}: approval must identify the human approver/reviewer")

    tie_fields = {
        "inventory_path",
        "trace_inventory_path",
        "trace_inventory",
        "inventory_sha256",
        "trace_inventory_sha256",
        "trace_count",
        "total_trace_count",
        "real_trace_count",
        "profile_root",
        "field_status_path",
        "field_status_sha256",
        "real_platform_field_status_path",
        "real_platform_field_status_sha256",
    }
    tie_values = find_values_by_key(approval, tie_fields)
    if not tie_values:
        failures.append(f"{path}: approval is not tied to a trace inventory path, hash, count, or profile root")

    path_values = find_values_by_key(approval, {"inventory_path", "trace_inventory_path", "trace_inventory"})
    if inventory is not None and path_values:
        accepted = {inventory_path.as_posix(), str(inventory_path), inventory_path.name}
        if not any(str(value).strip() in accepted or Path(str(value).strip()).name == inventory_path.name for value in path_values):
            failures.append(f"{path}: approval inventory path does not match {inventory_path}")

    inventory_hash_values = find_values_by_key(approval, {"inventory_sha256"})
    if not inventory_hash_values:
        failures.append(f"{path}: approval must record current inventory_sha256")
    elif not inventory_path.exists():
        failures.append(f"{path}: approval records inventory_sha256 but {inventory_path} is missing")
    else:
        digest = sha256_file(inventory_path)
        if not any(str(value).strip().lower() == digest for value in inventory_hash_values):
            failures.append(f"{path}: approval inventory sha256 does not match {inventory_path}")

    field_status = inventory.get("field_status") if isinstance(inventory, dict) else None
    field_hash_values = find_values_by_key(approval, {"real_platform_field_status_sha256"})
    if not field_hash_values:
        failures.append(f"{path}: approval must record real_platform_field_status_sha256")
    elif not isinstance(field_status, dict) or not field_status.get("sha256"):
        failures.append(f"{path}: approval records real_platform_field_status_sha256 but inventory has no field-status sha256")
    else:
        expected_hash = str(field_status.get("sha256", "")).strip().lower()
        if not any(str(value).strip().lower() == expected_hash for value in field_hash_values):
            failures.append(f"{path}: approval real_platform_field_status_sha256 does not match inventory field_status sha256")

    for value in find_values_by_key(approval, {"trace_count", "total_trace_count"}):
        expected = int_or_none(value)
        if expected is not None and expected != total_traces:
            failures.append(f"{path}: approved trace_count={expected}, scanned trace_count={total_traces}")
    for value in find_values_by_key(approval, {"real_trace_count"}):
        expected = int_or_none(value)
        if expected is not None and expected != real_traces:
            failures.append(f"{path}: approved real_trace_count={expected}, scanned real_trace_count={real_traces}")

    return not failures, failures, approval


def real_platform_field_status_failures(
    inventory_path: Path,
    inventory: dict[str, Any] | None,
    approval_valid: bool,
    approval: dict[str, Any] | None,
) -> list[str]:
    if inventory is None:
        return [f"missing {inventory_path}; cannot verify real-platform LLVM field status"]
    field_status = inventory.get("field_status")
    if not isinstance(field_status, dict):
        return [f"{inventory_path}: missing machine-readable field_status section"]
    if not field_status.get("exists"):
        return [f"{inventory_path}: missing real_platform_field_status.json artifact"]
    status = str(field_status.get("status", "missing"))
    if status in {"invalid", "no_records", "missing"}:
        detail = field_status.get("error") or status
        return [f"{inventory_path}: invalid real-platform field status artifact: {detail}"]
    unresolved_records = field_status_unresolved_records(field_status)
    unresolved_total = max(
        int_or_none(field_status.get("unresolved_total")) or 0,
        len(unresolved_records),
        field_status_blocking_count(field_status),
    )
    accepted = field_status_risks_accepted(field_status, approval)
    if unresolved_total and not (approval_valid and accepted):
        counts = Counter(
            str(record.get("status", "unknown"))
            for record in unresolved_records
            if isinstance(record, dict)
        )
        if not counts and isinstance(field_status.get("status_counts"), dict):
            counts = Counter(
                {
                    str(status): int_or_none(count) or 0
                    for status, count in field_status["status_counts"].items()
                    if is_blocking_field_status(status)
                }
            )
        suffix = ""
        if counts:
            suffix = " status_counts=" + json.dumps(counts, sort_keys=True)
        if approval_valid and not accepted:
            suffix += "; approval accepted risk scope is missing or incomplete"
        return [f"{inventory_path}: unresolved real-platform LLVM field-status risks={unresolved_total}{suffix}"]
    return []


def marker_contract_failures(inventory_path: Path, inventory: dict[str, Any] | None) -> list[str]:
    if inventory is None:
        return [f"missing {inventory_path}; cannot verify marker contract"]
    marker_contract = inventory.get("marker_contract")
    if not isinstance(marker_contract, dict):
        return [f"{inventory_path}: missing machine-readable marker_contract section"]
    if marker_contract.get("status") != "PASS":
        failures = marker_contract.get("failures")
        if failures:
            return [f"{inventory_path}: marker contract failed: {json.dumps(failures[:3], sort_keys=True)}"]
        return [f"{inventory_path}: marker contract status is {marker_contract.get('status', 'missing')}"]
    checked = int_or_none(marker_contract.get("checked_real_gem5_t00_traces")) or 0
    if checked <= 0:
        return [f"{inventory_path}: marker contract has no checked real gem5 T00 baseline traces"]
    return []


def waiver_dicts(data: Any) -> list[dict[str, Any]]:
    waivers: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if "waiver" in canonical_key(key).lower():
                if isinstance(value, dict):
                    waivers.append(value)
                elif isinstance(value, list):
                    waivers.extend(item for item in value if isinstance(item, dict))
            waivers.extend(waiver_dicts(value))
    elif isinstance(data, list):
        for value in data:
            waivers.extend(waiver_dicts(value))
    return waivers


def list_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def waiver_covers(waiver: dict[str, Any], expected: ExpectedExperiment) -> bool:
    scope_values = list_values(get_any(waiver, {"scope"})) + list_values(get_any(waiver, {"scopes"}))
    if any(value.lower() in ("all", "all_required_experiments", "*") for value in scope_values):
        return True
    experiment_ids = list_values(get_any(waiver, {"experiment_id"})) + list_values(get_any(waiver, {"experiment_ids"}))
    if expected.experiment_id in experiment_ids:
        return True
    template_ids = list_values(get_any(waiver, {"template_id"})) + list_values(get_any(waiver, {"template_ids"}))
    result_groups = list_values(get_any(waiver, {"result_group"})) + list_values(get_any(waiver, {"result_groups"}))
    if expected.template_id in template_ids and (not result_groups or expected.result_group in result_groups):
        return True
    return False


def has_repeat_waiver(expected: ExpectedExperiment, inventory: dict[str, Any] | None, approval: dict[str, Any] | None) -> bool:
    for waiver in waiver_dicts(inventory) + waiver_dicts(approval):
        requirement = " ".join(
            list_values(get_any(waiver, {"requirement"}))
            + list_values(get_any(waiver, {"type"}))
            + list_values(get_any(waiver, {"kind"}))
        ).lower()
        if not any(term in requirement for term in ("repeat", "stability", "repeatability")):
            continue
        status = get_any(waiver, {"approved", "status", "waived"})
        if not truthy_waiver_status(status):
            continue
        reason = get_any(waiver, {"reason", "justification"})
        if not str(reason or "").strip():
            continue
        if waiver_covers(waiver, expected):
            return True
    return False


def confidence_failures(inventory_path: Path, inventory: dict[str, Any] | None) -> list[str]:
    if inventory is None:
        return [f"missing {inventory_path}; cannot verify confidence for real-platform claimed fields"]
    failures: list[str] = []
    confidence_records: list[tuple[str, Any]] = []
    for path, item in walk_dicts(inventory):
        if item.get("claimed") is False:
            continue
        if "confidence" in item:
            value = item.get("confidence")
            if isinstance(value, dict):
                value = value.get("level", value.get("status", value.get("value")))
            confidence_records.append((path, value))
    if not confidence_records:
        return [f"{inventory_path}: no machine-readable confidence entries for claimed real-platform fields"]
    bad: list[str] = []
    for path, value in confidence_records:
        lowered = str(value).strip().lower() if value is not None else ""
        if (
            lowered in UNKNOWN_CONFIDENCE_VALUES
            or lowered.startswith("insufficient")
            or "unknown" in lowered
            or "synthetic" in lowered
        ):
            bad.append(f"{path}={value}")
    if bad:
        failures.append("confidence is unknown/insufficient/synthetic for claimed fields: " + ", ".join(bad[:8]))
    return failures


def conflict_status_failures(inventory_path: Path, inventory: dict[str, Any] | None) -> list[str]:
    if inventory is None:
        return [f"missing {inventory_path}; cannot verify that unresolved conflicts are absent"]
    found_status = False
    unresolved: list[str] = []
    for path, item in walk_dicts(inventory):
        for key, value in item.items():
            lowered_key = canonical_key(key).lower()
            if lowered_key in {"unresolved_conflicts", "open_conflicts", "conflicts"}:
                found_status = True
                if value in (False, 0, None, [], {}):
                    continue
                if isinstance(value, list):
                    for index, entry in enumerate(value):
                        if isinstance(entry, dict):
                            status = str(entry.get("status", entry.get("resolution", ""))).lower()
                            if status in {"resolved", "closed", "accepted", "waived"}:
                                continue
                        unresolved.append(f"{path}.{key}[{index}]")
                elif isinstance(value, dict):
                    items = value.get("items")
                    unresolved_total = int_or_none(
                        value.get("unresolved_total", value.get("unresolved_count", value.get("open_total")))
                    )
                    if items in (None, [], {}) and unresolved_total in (None, 0):
                        continue
                    if isinstance(items, list):
                        for index, entry in enumerate(items):
                            if isinstance(entry, dict):
                                status = str(entry.get("status", entry.get("resolution", ""))).lower()
                                if status in {"resolved", "closed", "accepted", "waived"}:
                                    continue
                            unresolved.append(f"{path}.{key}.items[{index}]")
                        continue
                    status = str(value.get("status", value.get("resolution", ""))).lower()
                    if status not in {"resolved", "closed", "accepted", "waived"}:
                        unresolved.append(f"{path}.{key}")
                else:
                    unresolved.append(f"{path}.{key}={value}")
    if not found_status:
        return [f"{inventory_path}: no machine-readable conflict status"]
    if unresolved:
        return ["unresolved conflicts remain: " + ", ".join(unresolved[:8])]
    return []


def has_documented_assumptions(text: str, inventory: dict[str, Any] | None) -> bool:
    if inventory is not None:
        assumptions = find_values_by_key(inventory, {"assumptions", "assumption"})
        if any(value not in (None, "", [], {}) for value in assumptions):
            return True
    lines = text.splitlines()
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("## assumptions"):
            in_section = True
            continue
        if in_section and stripped.startswith("##"):
            return False
        if in_section and stripped and not stripped.startswith("|"):
            return True
    return False


def t40_deferral_failures(
    text: str,
    inventory: dict[str, Any] | None,
    deferred_expected: list[ExpectedExperiment],
    real_counts: dict[str, int],
) -> list[str]:
    missing = [item for item in deferred_expected if real_counts.get(item.experiment_id, 0) == 0]
    if not missing:
        return []
    evidence_text = text.lower()
    if inventory is not None:
        evidence_text += "\n" + json.dumps(inventory, sort_keys=True).lower()
    documented = "t40" in evidence_text and ("defer" in evidence_text or "common" in evidence_text)
    if documented:
        return []
    examples = ", ".join(item.experiment_id for item in missing[:5])
    return [f"T40 common/deferred coverage is missing without documented deferral; examples: {examples}"]


def real_platform_failures(text: str, profile_root: Path) -> list[str]:
    lowered = text.lower()
    failures: list[str] = []
    if "mode: real_platform_profile" not in lowered:
        failures.append("quality report must declare `mode: real_platform_profile`")
    if not has_pass_status(text):
        failures.append("quality report must contain exact line `Gate status: PASS`")
    banned_phrases = (
        "predicted equals real",
        "real matches golden",
        "real equals golden",
        "matches configured ground truth",
        "matches synthetic golden",
    )
    for phrase in banned_phrases:
        if phrase in lowered:
            failures.append(f"real-platform report must not use golden-equality condition `{phrase}`")

    expected, deferred_expected = load_expected_experiments(profile_root)
    trace_observations, trace_failures = load_trace_observations(profile_root)
    failures.extend(trace_failures)
    inventory_path, inventory, inventory_failures = load_inventory(profile_root)
    failures.extend(inventory_failures)
    observations = trace_observations + inventory_observations(inventory, profile_root)
    real_counts = real_observation_counts(observations)
    real_trace_count = sum(1 for observation in trace_observations if is_real_gem5_observation(observation))
    approval_valid = False
    approval: dict[str, Any] | None = None

    if not expected:
        failures.append("no required generated experiments found for selected suite")
    else:
        missing_coverage = [item for item in expected if real_counts.get(item.experiment_id, 0) == 0]
        failures.extend(summarize_expected_missing("real gem5 coverage", expected, missing_coverage))

        approval_valid, approval_failures, approval = human_approval_failures(
            profile_root, inventory_path, inventory, len(trace_observations), real_trace_count
        )
        failures.extend(approval_failures)
        missing_repeats = [
            item
            for item in expected
            if real_counts.get(item.experiment_id, 0) < 2
            and not (approval_valid and has_repeat_waiver(item, inventory, approval))
        ]
        failures.extend(summarize_expected_missing("repeatability/stability", expected, missing_repeats))

    failures.extend(real_platform_field_status_failures(inventory_path, inventory, approval_valid, approval))
    failures.extend(marker_contract_failures(inventory_path, inventory))
    failures.extend(confidence_failures(inventory_path, inventory))
    failures.extend(conflict_status_failures(inventory_path, inventory))
    if not has_documented_assumptions(text, inventory):
        failures.append("documented assumptions are missing from quality report or real-platform inventory")
    failures.extend(t40_deferral_failures(text, inventory, deferred_expected, real_counts))
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check synthetic or real-platform calibration gate.")
    parser.add_argument("--mode", required=True, choices=("synthetic_calibration", "real_platform_profile"))
    parser.add_argument("--mismatch-report", default="results/common/mismatch_report.md")
    parser.add_argument("--quality-report", default="results/common/experiment_quality.md")
    parser.add_argument("--profile-root", default="results")
    parser.add_argument("--config", default="config/rvv_timing_model.yaml")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "synthetic_calibration":
            report_path = Path(args.mismatch_report)
            failures = synthetic_failures(read_text(report_path), Path(args.profile_root), Path(args.config))
        else:
            report_path = Path(args.quality_report)
            failures = real_platform_failures(read_text(report_path), Path(args.profile_root))
    except FileNotFoundError as error:
        print(f"FAIL: {error}")
        return 2

    if failures:
        print(f"FAIL: {args.mode} gate did not pass using {report_path}")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"PASS: {args.mode} gate passed using {report_path}")
    if args.mode == "real_platform_profile":
        print("Real-platform mode checked real gem5 coverage, repeats, confidence, conflicts, assumptions, and approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
