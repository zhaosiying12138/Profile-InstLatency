# RVV Instruction Latency Profiling

This repository is the bootstrap workspace for profiling selected non-memory RVV instruction timing and preserving results in a shape that can later inform an LLVM RISC-V schedule model. The current checkout contains environment gating, LLVM field extraction, assembly-generation scaffolds, dry-run runner traces, analysis/search scaffolds, calibration gates, and Humanize2 replay artifacts.

## Setup

1. Edit `config/paths.yaml` for this machine.
2. Keep external checkout paths absolute when possible. Repo-relative paths are also accepted by `scripts/check_env.py`.
3. Run the environment check:

```bash
python3 scripts/check_env.py
```

The script uses only the Python standard library. It prints a JSON report to stdout. The default `plan` command is strict: it requires `llvm_checkout`, `gem5_checkout`, `gem5_build`, `assembler`, `linker`, and `output_root` to resolve on this machine.

For scaffold-only or dry-run work, the missing-tool policy must be explicit:

```bash
python3 scripts/check_env.py --allow-dry-run-missing-tools
python3 scripts/check_env.py --command dry_run
```

Those commands validate dry-run readiness only. They do not prove real platform profiling readiness.

## One-Command Overview

Current strict environment gate:

```bash
python3 scripts/check_env.py
```

Current synthetic/scaffold replay path:

```bash
python3 scripts/check_env.py
python3 scripts/gen_asm.py suite --manifest-only
python3 scripts/run_suite.py --killcheck --dry-run
python3 scripts/analyze.py --all --dry-run
python3 scripts/search_model.py --profile results/common --format markdown
python3 scripts/check_calibration_gate.py --mode synthetic_calibration
python3 scripts/prepare_llvm_yushuxin_worktree.py --tag llvmorg-22.1.3 --cpu YuShuXin
```

The non-dry-run platform path is not accepted by dry-run artifacts. It must wait for real gem5 marker/timing integration and kill-check evidence before these commands can be treated as platform profiling:

```bash
python3 scripts/check_env.py
python3 scripts/run_suite.py --killcheck
python3 scripts/run_suite.py --all
python3 scripts/analyze.py --all
python3 scripts/search_model.py --profile results --format markdown
```

## Modes

`mode: synthetic_calibration`

Use this for the synthetic calibration loop. It is allowed to compare inferred values against configured ground truth because the purpose is to debug the workflow, experiment templates, schemas, and inference logic. Dry-run traces and synthetic calibration gates are scaffold evidence, not real platform evidence.

`mode: real_platform_profile`

Use this for real platform profiling. This mode must not use predicted-equals-real as a loop condition. Completion is based on real simulator or platform traces, coverage, repeatability, confidence, documented assumptions, and explicit human approval before any LLVM implementation phase.

## Configuration

`config/paths.yaml` is intentionally simple YAML-ish key/value data so `scripts/check_env.py` does not need PyYAML. Supported values are strings, quoted strings, empty values, `null`, and `~`.

Important keys:

- `mode`: `synthetic_calibration` or `real_platform_profile`.
- `llvm_checkout`: LLVM checkout used as a read-only schedule-model reference.
- `gem5_checkout`: gem5 source checkout used for RVV MinorCPU work.
- `gem5_build`: built gem5 executable such as `build/RISCV/gem5.opt`; required by the default strict gate.
- `assembler`: RISC-V assembler path; required by the default strict gate.
- `linker`: RISC-V linker path; required by the default strict gate.
- `output_root`: repository-local result root, normally `results`.

If gem5 RVV stability cannot be proven in the current round, record simulator evidence and fallback candidates in `docs/simulator-candidate-comparison.md`.

## RLCR And Humanize2 Notes

This repository is being implemented under Humanize RLCR agent teams. Worker agents should stay inside their assigned write scope, avoid `.humanize/rlcr/**`, and leave coordinator setup, gate, and cancel commands to the leader.

Humanize2 replay artifacts should preserve both modes. Synthetic calibration may loop against configured ground truth; real platform profiling must produce a confidence report and ask for explicit human approval before LLVM-facing implementation work.
