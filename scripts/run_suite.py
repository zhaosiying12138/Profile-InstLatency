#!/usr/bin/env python3
"""Run RVV profiling experiment suites through the shared runner."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from run_experiment import (
    INSTRUCTION_SET,
    ExperimentError,
    run_experiment_dir,
    run_experiment_from_metadata,
)


LMULS = ("m1", "m2", "m4")


def killcheck_metadata(instruction_id: str, lmul: str) -> dict[str, object]:
    info = INSTRUCTION_SET[instruction_id]
    return {
        "schema_version": 1,
        "experiment_id": f"T01_DECODE_EXEC_KILLCHECK-{instruction_id}-{lmul}",
        "template_id": "T01_DECODE_EXEC_KILLCHECK",
        "result_group": "common",
        "instruction": {
            "id": instruction_id,
            "asm": info["asm"],
            "llvm_sched_write": info["sched_write"],
            "sew": 32,
        },
        "lmul": lmul,
        "markers": ["before", "after", "program_end"],
        "expected": {
            "assemble": True,
            "execute": True,
            "markers_present": ["before", "after"],
            "program_end": True,
        },
    }


def baseline_marker_metadata() -> dict[str, object]:
    return {
        "schema_version": 1,
        "experiment_id": "T00_BASELINE_MARKER-common",
        "template_id": "T00_BASELINE_MARKER",
        "result_group": "common",
        "instruction_id": "vadd_vv",
        "lmul": "m1",
        "markers": ["t0", "t1"],
        "expected": {"marker_delta_cycles": 0},
    }


def instruction_template_metadata(
    template_id: str, instruction_id: str, lmul: str, *, result_group: str | None = None
) -> dict[str, object]:
    info = INSTRUCTION_SET[instruction_id]
    short_template = template_id.split("_", 1)[0]
    return {
        "schema_version": 1,
        "experiment_id": f"{short_template}-{instruction_id}-{lmul}",
        "template_id": template_id,
        "result_group": result_group or instruction_id,
        "instruction": {
            "id": instruction_id,
            "asm": info["asm"],
            "llvm_sched_write": info["sched_write"],
            "sew": 32,
        },
        "lmul": lmul,
        "markers": ["start", "end"],
    }


def common_load_metadata() -> dict[str, object]:
    return {
        "schema_version": 1,
        "experiment_id": "T40_COMMON_VLSU_LOAD_HIT-m1",
        "template_id": "T40_COMMON_VLSU_LOAD_HIT",
        "result_group": "common",
        "instruction_id": "vadd_vv",
        "lmul": "m1",
        "markers": ["start", "end"],
        "status": "scaffold_only",
    }


def generated_source_for(metadata: dict[str, object], generated_root: Path) -> Path | None:
    experiment_id = str(metadata["experiment_id"])
    candidate = generated_root / experiment_id
    if (candidate / "experiment.yaml").exists():
        return candidate
    return None


def run_metadata_or_generated(
    metadata: dict[str, object],
    *,
    args: argparse.Namespace,
) -> Path:
    source_dir = generated_source_for(metadata, args.generated_root)
    if source_dir:
        return run_experiment_dir(
            source_dir,
            dry_run=args.dry_run,
            results_root=args.results_root,
            timing_model_path=args.timing_model,
        )
    return run_experiment_from_metadata(
        metadata,
        dry_run=args.dry_run,
        results_root=args.results_root,
        timing_model_path=args.timing_model,
    )


def build_killcheck_suite() -> list[dict[str, object]]:
    return [
        killcheck_metadata(instruction_id, lmul)
        for instruction_id in INSTRUCTION_SET
        for lmul in LMULS
    ]


def build_all_suite() -> list[dict[str, object]]:
    suite: list[dict[str, object]] = [baseline_marker_metadata()]
    suite.extend(build_killcheck_suite())
    for instruction_id in INSTRUCTION_SET:
        for lmul in LMULS:
            suite.append(
                instruction_template_metadata(
                    "T10_INDEPENDENT_STREAM_THROUGHPUT", instruction_id, lmul
                )
            )
            suite.append(instruction_template_metadata("T11_SELF_RAW_CHAIN", instruction_id, lmul))
            suite.append(instruction_template_metadata("T30_LMUL_SCALING", instruction_id, lmul))
    suite.append(common_load_metadata())
    return suite


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    suite = parser.add_mutually_exclusive_group(required=True)
    suite.add_argument("--killcheck", action="store_true", help="run only T01 kill-checks")
    suite.add_argument("--all", action="store_true", help="run common and instruction suites")
    parser.add_argument("--dry-run", action="store_true", help="write deterministic synthetic traces")
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
        help="RVV timing model used for dry-run synthetic traces",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    suite = build_killcheck_suite() if args.killcheck else build_all_suite()
    outputs: list[Path] = []
    try:
        for metadata in suite:
            outputs.append(run_metadata_or_generated(metadata, args=args))
    except ExperimentError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
