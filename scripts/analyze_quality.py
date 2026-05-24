#!/usr/bin/env python3
"""Real-platform quality inventory and report helpers for RVV analysis."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterable

from analyze_core import (
    APPROVAL_FILENAMES,
    BLOCKING_FIELD_STATUSES,
    FIELD_STATUS_FILENAME,
    NON_REQUIRED_REAL_TEMPLATES,
    QUALITY_ASSUMPTIONS,
    REQUIRED_REAL_LLVM_FIELDS,
    RUN_RESULT_DIR_RE,
    ExperimentAnalysis,
    bool_or_false,
    first_value,
    int_or_none,
    parse_yamlish,
    render_yaml,
    truthy_human_approval_status,
)

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


def top_level_values_by_key(data: Any, names: set[str]) -> list[Any]:
    if not isinstance(data, dict):
        return []
    return [value for key, value in data.items() if canonical_json_key(key) in names]


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
                    approval_values = top_level_values_by_key(
                        data,
                        {
                            "approved",
                            "human_approved",
                            "human_approval",
                            "status",
                            "human_approval_status",
                            "approval_status",
                        },
                    )
                    status_value = str(
                        first_value(
                            *top_level_values_by_key(
                                data, {"status", "human_approval_status", "approval_status"}
                            ),
                            "",
                        )
                    ).lower()
                    artifact["approved"] = bool(approval_values) and all(
                        truthy_human_approval_status(value) for value in approval_values
                    )
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
