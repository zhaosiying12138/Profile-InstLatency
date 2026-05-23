#!/usr/bin/env python3
"""Run RVV profiling experiment suites through the shared runner."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from run_experiment import (
    COMMON_TEMPLATES,
    ExperimentError,
    load_structured_file,
    result_group as experiment_result_group,
    run_experiment_dir,
)


KILLCHECK_TEMPLATE = "T01_DECODE_EXEC_KILLCHECK"


def positive_int(text: str) -> int:
    value = int(text, 10)
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value


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
    entries = apply_selection_filters(entries, args)
    if not entries:
        if has_selection_filters(args):
            raise ExperimentError("selection filters matched no experiments")
        raise ExperimentError("selected suite is empty")
    return entries


def has_selection_filters(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "template_id", None) or getattr(args, "id_regex", None))


def compile_id_regexes(patterns: list[str]) -> list[re.Pattern[str]]:
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as error:
            raise ExperimentError(f"invalid --id-regex {pattern!r}: {error}") from error
    return compiled


def apply_selection_filters(
    entries: list[dict[str, Any]], args: argparse.Namespace
) -> list[dict[str, Any]]:
    template_ids = set(getattr(args, "template_id", []) or [])
    patterns = compile_id_regexes(list(getattr(args, "id_regex", []) or []))
    filtered = entries
    if template_ids:
        filtered = [entry for entry in filtered if str(entry.get("template_id")) in template_ids]
    for pattern in patterns:
        filtered = [entry for entry in filtered if pattern.search(str(entry.get("id")))]
    return filtered


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


def repeat_result_root(base_root: Path, repeat_index: int, repeat_count: int) -> Path:
    if repeat_count == 1:
        return base_root
    width = max(2, len(str(repeat_count)))
    return base_root / f"r{repeat_index:0{width}d}"


def entry_result_group(entry: dict[str, Any], generated_root: Path) -> str:
    group = entry.get("result_group")
    if group:
        return str(group)
    template_id = str(entry.get("template_id"))
    if template_id in COMMON_TEMPLATES:
        return "common"
    instruction_id = entry.get("instruction_id")
    if instruction_id:
        return str(instruction_id)
    source_dir = generated_root / str(entry["id"])
    metadata_path = source_dir / "experiment.yaml"
    if metadata_path.exists():
        metadata = load_structured_file(metadata_path)
        if isinstance(metadata, dict):
            return experiment_result_group(metadata)
    return "common"


def result_trace_path(entry: dict[str, Any], args: argparse.Namespace, repeat_index: int) -> Path:
    results_root = repeat_result_root(args.results_root, repeat_index, args.repeat)
    return (
        results_root
        / entry_result_group(entry, args.generated_root)
        / "experiments"
        / str(entry["id"])
        / "trace.json"
    )


def selected_run_items(args: argparse.Namespace) -> list[tuple[int, dict[str, Any]]]:
    entries = selected_entries(args)
    missing_only = bool(getattr(args, "missing", False))
    items: list[tuple[int, dict[str, Any]]] = []
    for repeat_index in range(1, args.repeat + 1):
        for entry in entries:
            if missing_only and result_trace_path(entry, args, repeat_index).exists():
                continue
            items.append((repeat_index, entry))
    if not items:
        raise ExperimentError("selection filters matched no missing experiment results")
    return items


def run_generated_entry(entry: dict[str, Any], args: argparse.Namespace, repeat_index: int) -> Path:
    source_dir = generated_source_for(entry, args.generated_root)
    mode = args.mode
    backend = args.backend
    if backend == "auto" and args.killcheck and not args.dry_run:
        mode = "real_platform_profile"
        backend = "gem5_minor"
    results_root = repeat_result_root(args.results_root, repeat_index, args.repeat)
    return run_experiment_dir(
        source_dir,
        dry_run=args.dry_run,
        results_root=results_root,
        timing_model_path=args.timing_model,
        mode=mode,
        backend=backend,
        repeat_index=repeat_index if args.repeat > 1 else None,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    suite = parser.add_mutually_exclusive_group(required=True)
    suite.add_argument("--killcheck", action="store_true", help="run only generated T01 kill-checks")
    suite.add_argument("--all", action="store_true", help="run every generated experiment")
    parser.add_argument(
        "--template-id",
        action="append",
        default=[],
        help="only run manifest entries with this template ID; repeat to allow multiple IDs",
    )
    parser.add_argument(
        "--id-regex",
        action="append",
        default=[],
        help="only run manifest entries whose id matches this regex; repeated regexes must all match",
    )
    parser.add_argument(
        "--missing",
        action="store_true",
        help="only run repeat entries whose expected trace.json is absent under the selected results root",
    )
    parser.add_argument("--dry-run", action="store_true", help="write deterministic synthetic trace files")
    parser.add_argument(
        "--mode",
        choices=("synthetic_calibration", "real_platform_profile"),
        default="synthetic_calibration",
        help=(
            "execution mode; synthetic_calibration uses the stdlib synthetic cmodel "
            "except kill-check auto backend, which runs gem5 MinorCPU"
        ),
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "synthetic_cmodel", "gem5_minor"),
        default="auto",
        help="execution backend; auto runs gem5 for kill-checks and synthetic cmodel for full calibration",
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
    parser.add_argument(
        "--repeat",
        type=positive_int,
        default=1,
        help="number of complete suite repetitions to run; N>1 writes under <results-root>/rXX",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    outputs: list[Path] = []
    try:
        for repeat_index, entry in selected_run_items(args):
            outputs.append(run_generated_entry(entry, args, repeat_index))
    except ExperimentError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
