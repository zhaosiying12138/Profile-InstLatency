#!/usr/bin/env python3
"""Run RVV profiling experiment suites through the shared runner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from run_experiment import (
    ExperimentError,
    load_structured_file,
    run_experiment_dir,
)


KILLCHECK_TEMPLATE = "T01_DECODE_EXEC_KILLCHECK"


def load_manifest_entries(generated_root: Path) -> list[dict[str, Any]]:
    manifest_path = generated_root / "suite_manifest.yaml"
    if not manifest_path.exists():
        raise ExperimentError(
            f"missing generated suite manifest: {manifest_path}; "
            "run `python3 scripts/gen_asm.py suite` first"
        )
    manifest = load_structured_file(manifest_path)
    if not isinstance(manifest, dict):
        raise ExperimentError(f"suite manifest must be a mapping: {manifest_path}")
    entries = manifest.get("experiments")
    if not isinstance(entries, list):
        raise ExperimentError(f"suite manifest missing experiments list: {manifest_path}")
    normalized: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ExperimentError(f"suite manifest contains a non-mapping entry: {entry!r}")
        if not entry.get("id"):
            raise ExperimentError(f"suite manifest entry missing id: {entry!r}")
        if not entry.get("template_id"):
            raise ExperimentError(f"suite manifest entry missing template_id: {entry!r}")
        normalized.append(entry)
    return normalized


def selected_entries(args: argparse.Namespace) -> list[dict[str, Any]]:
    entries = load_manifest_entries(args.generated_root)
    if args.killcheck:
        entries = [entry for entry in entries if entry.get("template_id") == KILLCHECK_TEMPLATE]
    if not entries:
        raise ExperimentError("selected suite is empty")
    return entries


def generated_source_for(entry: dict[str, Any], generated_root: Path) -> Path:
    experiment_id = str(entry["id"])
    source_dir = generated_root / experiment_id
    metadata_path = source_dir / "experiment.yaml"
    assembly_path = source_dir / "test.s"
    if metadata_path.exists() and assembly_path.exists():
        return source_dir
    raise ExperimentError(
        f"generated source for {experiment_id!r} is incomplete under {source_dir}; "
        "run `python3 scripts/gen_asm.py suite` to materialize the full suite"
    )


def run_generated_entry(entry: dict[str, Any], args: argparse.Namespace) -> Path:
    source_dir = generated_source_for(entry, args.generated_root)
    return run_experiment_dir(
        source_dir,
        dry_run=args.dry_run,
        results_root=args.results_root,
        timing_model_path=args.timing_model,
        mode=args.mode,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    suite = parser.add_mutually_exclusive_group(required=True)
    suite.add_argument("--killcheck", action="store_true", help="run only generated T01 kill-checks")
    suite.add_argument("--all", action="store_true", help="run every generated experiment")
    parser.add_argument("--dry-run", action="store_true", help="write labeled scaffold traces")
    parser.add_argument(
        "--mode",
        choices=("synthetic_calibration", "real_platform_profile"),
        default="synthetic_calibration",
        help="execution mode; synthetic_calibration uses the stdlib synthetic cmodel",
    )
    parser.add_argument(
        "--generated-root",
        type=Path,
        default=Path("experiments/generated"),
        help="root containing generated experiment directories",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("results"),
        help="root where normalized experiment results are written",
    )
    parser.add_argument(
        "--timing-model",
        type=Path,
        default=Path("config/rvv_timing_model.yaml"),
        help="RVV timing model used for synthetic traces",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    outputs: list[Path] = []
    try:
        for entry in selected_entries(args):
            outputs.append(run_generated_entry(entry, args))
    except ExperimentError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
