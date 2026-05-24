#!/usr/bin/env python3
"""Analyze RVV profiling traces and synthesize LLVM-facing profiles.

The analyzer is stdlib-only and intentionally conservative. Claimed LLVM
timing fields come from raw marker deltas plus experiment metadata. Synthetic
dry-run traces may carry configured timing metadata, but that metadata is used
only as reference material for calibration mismatch reports and trace notes.
Fields without enough non-circular marker evidence are left explicit and
unclaimed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analyze_core import *  # noqa: F401,F403
from analyze_quality import *  # noqa: F401,F403

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze RVV marker trace JSON files.")
    parser.add_argument("--all", action="store_true", help="Accepted for the plan's one-command flow.")
    parser.add_argument("--root", default="results", help="Result root to scan.")
    parser.add_argument("--config", default="config/rvv_timing_model.yaml", help="Synthetic timing config.")
    parser.add_argument(
        "--aggregate",
        default=None,
        help="Real-platform quality report path.",
    )
    parser.add_argument(
        "--mismatch-report",
        default=None,
        help="Synthetic calibration mismatch report path.",
    )
    parser.add_argument(
        "--inventory",
        default=None,
        help="Real-platform machine-readable inventory path. Defaults next to --aggregate.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without changing files.")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if args.aggregate is None:
        args.aggregate = (root / "common" / "experiment_quality.md").as_posix()
    if args.mismatch_report is None:
        args.mismatch_report = (root / "common" / "mismatch_report.md").as_posix()
    return args


def main() -> int:
    args = parse_args()
    root = Path(args.root)
    trace_paths = find_traces(root)
    analyses = [analyze_trace(path) for path in trace_paths]
    synthetic_profile_analyses = [
        item for item in analyses if is_main_synthetic_calibration_trace(item, root)
    ]
    timing_config = load_timing_config(Path(args.config))
    config_instructions = timing_config.get("instructions") if isinstance(timing_config.get("instructions"), dict) else {}

    by_instruction = build_instruction_index(synthetic_profile_analyses)

    instruction_order = list(config_instructions) if isinstance(config_instructions, dict) else sorted(by_instruction)
    profiles: dict[str, dict[str, Any]] = {}
    for instruction_id in instruction_order:
        config_instr = config_instructions.get(instruction_id) if isinstance(config_instructions, dict) else None
        profiles[instruction_id] = build_profile(
            instruction_id,
            by_instruction.get(instruction_id, []),
            config_instr,
            by_instruction,
        )

    rows, failures = compare_profiles_to_config(profiles, timing_config)
    inventory = build_quality_inventory(analyses, root)
    inventory_path = Path(args.inventory) if args.inventory else Path(args.aggregate).with_name("real_platform_inventory.json")
    inventory["inventory_path"] = inventory_path.as_posix()

    writes: list[tuple[Path, str]] = []
    for item in analyses:
        writes.append((item.trace_path.parent / "analysis.md", render_experiment_markdown(item)))
    for instruction_id, profile in profiles.items():
        writes.append((root / instruction_id / "profile.yaml", render_profile_yaml(profile)))
    writes.append((inventory_path, json.dumps(inventory, indent=2, sort_keys=True) + "\n"))
    writes.append((Path(args.aggregate), render_quality_report(inventory)))
    writes.append((Path(args.mismatch_report), render_mismatch_report(rows, failures)))

    if args.dry_run:
        for path, _content in writes:
            print(f"would write {path}")
        return 0

    for path, content in writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
