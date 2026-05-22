# RVV Instruction Latency Profiling

This repository is the bootstrap workspace for profiling selected non-memory RVV instruction timing and preserving results in a shape that can later inform an LLVM RISC-V schedule model. Phase 0 sets up the repository-local configuration and environment check; later phases add LLVM field extraction, gem5 kill-checks, experiment generation, analysis, and export.

## Setup

1. Edit `config/paths.yaml` for this machine.
2. Keep external checkout paths absolute when possible. Repo-relative paths are also accepted by `scripts/check_env.py`.
3. Run the environment check:

```bash
python3 scripts/check_env.py
```

The script uses only the Python standard library. It prints a JSON report to stdout and exits non-zero only for bootstrap blockers such as a missing config file, an invalid mode, or an unsupported Python runtime. External tool paths are reported as present, missing, or unspecified so Phase 0 can land before every toolchain component is installed.

## One-Command Overview

Current Phase 0 smoke check:

```bash
python3 scripts/check_env.py
```

The eventual empty-context handoff from `docs/plan.md` is:

```bash
python3 scripts/check_env.py
python3 scripts/run_suite.py --killcheck
python3 scripts/run_suite.py --all
python3 scripts/analyze.py --all
python3 scripts/export_llvm_draft.py
```

Only `check_env.py` exists in Phase 0.

## Modes

`mode: synthetic_calibration`

Use this for the synthetic gem5/cmodel calibration loop. It is allowed to compare inferred values against configured ground truth because the purpose is to debug the workflow, experiment templates, schemas, and inference logic.

`mode: real_platform_profile`

Use this for real platform profiling. This mode must not use predicted-equals-real as a loop condition. Completion is based on coverage, repeatability, confidence, documented assumptions, and explicit human approval before any LLVM implementation phase.

## Configuration

`config/paths.yaml` is intentionally simple YAML-ish key/value data so `scripts/check_env.py` does not need PyYAML. Supported values are strings, quoted strings, empty values, `null`, and `~`.

Important keys:

- `mode`: `synthetic_calibration` or `real_platform_profile`.
- `llvm_checkout`: LLVM checkout used as a read-only schedule-model reference.
- `gem5_checkout`: gem5 source checkout used for RVV MinorCPU work.
- `gem5_build`: optional built gem5 executable such as `build/RISCV/gem5.opt`.
- `assembler`: optional RISC-V assembler path.
- `linker`: optional RISC-V linker path.
- `output_root`: repository-local result root, normally `results`.

## RLCR And Humanize2 Notes

This repository is being implemented under Humanize RLCR agent teams. Worker agents should stay inside their assigned write scope, avoid `.humanize/rlcr/**`, and leave coordinator setup, gate, and cancel commands to the leader.

Humanize2 replay artifacts should preserve both modes. Synthetic calibration may loop against configured ground truth; real platform profiling must produce a confidence report and ask for explicit human approval before LLVM-facing implementation work.
