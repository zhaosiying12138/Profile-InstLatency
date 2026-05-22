#!/usr/bin/env python3
"""Check whether profiling results are ready to advance.

Synthetic calibration uses a mismatch report and may check configured ground
truth status. Real-platform profiling never checks golden equality; it checks
the wording and status of coverage/confidence evidence instead.
"""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_REAL_TERMS = (
    "coverage",
    "stability",
    "confidence",
    "assumptions",
    "human approval",
)


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing required report: {path}")
    return path.read_text(encoding="utf-8")


def has_pass_status(text: str) -> bool:
    return any(line.strip().lower() == "gate status: pass" for line in text.splitlines())


def synthetic_failures(text: str) -> list[str]:
    lowered = text.lower()
    failures: list[str] = []
    if "mode: synthetic_calibration" not in lowered:
        failures.append("mismatch report must declare `mode: synthetic_calibration`")
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
    banned_phrases = (
        "predicted equals real",
        "real matches golden",
        "real equals golden",
        "matches configured ground truth",
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "synthetic_calibration":
            report_path = Path(args.mismatch_report)
            failures = synthetic_failures(read_text(report_path))
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
        print("Real-platform mode checked coverage/confidence wording only; no golden equality was evaluated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
