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

REQUIRED_REAL_TERMS = (
    "coverage",
    "stability",
    "confidence",
    "assumptions",
    "human approval",
)


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


def has_explicit_human_approval(text: str) -> bool:
    approved_values = ("approved", "granted", "yes", "true", "pass")
    for line in text.splitlines():
        lowered = line.strip().lower()
        if not lowered.startswith("human approval"):
            continue
        if ":" not in lowered:
            continue
        value = lowered.split(":", 1)[1].strip()
        if value in approved_values or value.startswith("granted ") or value.startswith("approved "):
            return True
    return False


def real_platform_failures(text: str) -> list[str]:
    lowered = text.lower()
    failures: list[str] = []
    if "mode: real_platform_profile" not in lowered:
        failures.append("quality report must declare `mode: real_platform_profile`")
    if not has_pass_status(text):
        failures.append("quality report must contain exact line `Gate status: PASS`")
    for term in REQUIRED_REAL_TERMS:
        if term not in lowered:
            failures.append(f"quality report must discuss `{term}`")
    if not has_explicit_human_approval(text):
        failures.append("quality report must contain explicit `Human approval: granted` or equivalent")
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
            failures = real_platform_failures(read_text(report_path))
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
        print("Real-platform mode checked coverage/confidence/human approval only; no golden equality was evaluated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
