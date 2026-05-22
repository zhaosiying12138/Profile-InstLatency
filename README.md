# RVV Instruction Latency Profiling

This repository profiles selected non-memory RVV instruction timing and preserves results in a shape that can later inform an LLVM RISC-V schedule model. The current checkout contains environment gating, LLVM field extraction, deterministic assembly generation, synthetic and gem5 runners, analysis/search, calibration gates, Humanize2 replay artifacts, and LLVM YuShuXin implementation evidence.

## Setup

1. Edit `config/paths.yaml` for this machine.
2. Keep external checkout paths absolute when possible. Repo-relative paths are also accepted by `scripts/check_env.py`.
3. Run the environment check:

```bash
python3 scripts/check_env.py
```

The script uses only the Python standard library. It prints a JSON report to stdout. The default `plan` command is strict: it requires `llvm_checkout`, `gem5_checkout`, `gem5_build`, `assembler`, `linker`, and `output_root` to resolve on this machine.

For dry-run work, the missing-tool policy must be explicit:

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

Current synthetic calibration plus gem5 kill-check replay path:

```bash
python3 scripts/check_env.py
python3 scripts/gen_asm.py suite --manifest-only
python3 scripts/run_suite.py --all --backend synthetic_cmodel --results-root results
python3 scripts/run_suite.py --killcheck --backend gem5_minor --results-root results
python3 scripts/analyze.py --all --root results
python3 scripts/search_model.py --profile results --format markdown
python3 scripts/check_calibration_gate.py --mode synthetic_calibration
python3 scripts/prepare_llvm_yushuxin_worktree.py --tag llvmorg-22.1.3 --cpu YuShuXin
```

The full real-platform path is not accepted by the synthetic calibration gate. It must wait for real gem5 or hardware coverage of the latency/resource templates, repeated measurements, confidence review, and human approval. Repeated gem5 measurements use `--repeat N`; for `N > 1`, outputs are written under `<results-root>/rXX/...` and traces include a 1-based `repeat_index`:

```bash
python3 scripts/check_env.py
python3 scripts/run_suite.py --killcheck --backend gem5_minor --mode real_platform_profile --results-root results_repeat --repeat 2
python3 scripts/run_suite.py --all --backend gem5_minor --mode real_platform_profile --results-root results_repeat --repeat 2
python3 scripts/analyze.py --all --root results_repeat/r01
python3 scripts/analyze.py --all --root results_repeat/r02
python3 scripts/search_model.py --profile results_repeat/r01 --format markdown
```

## Modes

`mode: synthetic_calibration`

Use this for the synthetic calibration loop. It is allowed to compare inferred values against configured ground truth because the purpose is to debug the workflow, experiment templates, schemas, and inference logic. Synthetic traces and synthetic calibration gates are workflow calibration evidence, not full real-platform evidence.

`mode: real_platform_profile`

Use this for real platform profiling. This mode must not use predicted-equals-real as a loop condition. Completion is based on real simulator or platform traces, coverage, repeatability, confidence, documented assumptions, and explicit human approval before any LLVM implementation phase.

The gem5 MinorCPU runner lowers `TIMESTAMP_MARK <label>` pseudo-lines to zero-cost labels at the next instruction PC. It resolves those label addresses in the linked ELF and reads marker cycles from the first matching PC in gem5 `Exec` logs. T00 is the marker-only baseline for this method; adjacent marker labels should record the same cycle and keep `marker_baseline_cycles: 0`. This method depends on `Exec` logging, the configured 1 GHz gem5 clock, and visible marker PCs in the executed trace.

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
