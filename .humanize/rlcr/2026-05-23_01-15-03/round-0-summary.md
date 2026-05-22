# Round 0/1 Summary

## What Was Implemented

- Built the runnable RVV profiling workflow described by `docs/plan.md`: LLVM field extraction, deterministic RVV assembly generation, zero-cost marker lowering, synthetic cmodel runner, gem5 MinorCPU kill-check runner, analyzer, parameter search, synthetic calibration gate, real-platform quality gate, and Humanize2-style replay capture.
- Generated the 10-instruction `SEW=e32`, `LMUL={m1,m2,m4}` suite with 3221 experiments. T10/T11 now include multiple stream lengths and T12/T30 include K=0..40 readiness sweeps.
- Implemented non-circular profile inference: claimed LLVM-facing latency, `ReleaseAtCycles`, pipe affinity, resource group, and formula fits come from raw marker deltas. `trace.synthetic` is reference-only for post-inference mismatch checking.
- Ran `results/` end to end: full synthetic cmodel suite, gem5 MinorCPU T01 kill-check for 10 instructions x 3 LMUL, analyzer, search, and gates.
- Created and updated the isolated LLVM 22.1.3 `YuShuXin` RISC-V schedule-model worktree after synthetic calibration passed. A follow-up LLVM commit strengthens llvm-mca checks for all 30 profiled RVV rows.

## Key Evidence

- Synthetic calibration: `results/common/mismatch_report.md` reports `Gate status: PASS` and `Claimed mismatches: none`.
- Real-platform quality: `results/common/experiment_quality.md` reports `Gate status: NOT_READY`, with 30 gem5 T01 traces and no full timing-suite approval.
- Result shape: 3221 `trace.json` files and 3221 `analysis.md` files under `results/`.
- gem5 kill-check: `results/common/experiments/t01-*/trace.json` records `backend: gem5_minor`, `mode: real_platform_profile`, and `dry_run_trace: false`.
- Replay capture: `results/common/agentic_flow/replay.md`, boards, events, cartridge, worker outputs, and `artifacts/verification/coordinator-r1.md`.
- LLVM evidence: `results/common/llvm_yushuxin_implementation.md`; LLVM commits `16b310c4d252` and `13a8f69179f0`.

## Validation

- `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py`: passed.
- `python3 scripts/run_suite.py --all --backend synthetic_cmodel --results-root results`: passed.
- `python3 scripts/run_suite.py --killcheck --backend gem5_minor --results-root results`: passed.
- `python3 scripts/analyze.py --all --root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results --mismatch-report results/common/mismatch_report.md`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results --quality-report results/common/experiment_quality.md`: failed closed as expected because human approval and full real timing coverage are absent.
- `python3 scripts/search_model.py --profile results --format json --output /tmp/profile-inst-latency-r1-search.json`: passed.
- LLVM worktree focused tests passed:
  - `llvm-mca ... rvv-e32-profiled.s | FileCheck rvv-e32-profiled.s`
  - `llc -verify-machineinstrs ... yushuxin-rvv-codegen.ll | FileCheck yushuxin-rvv-codegen.ll`
  - `git diff --check`

## Remaining Items

- No blocking item remains for the synthetic calibration branch of this RLCR task.
- Real Paladin/full gem5 profiling remains intentionally gated by AC-16: coverage, repeated measurements, confidence, documented assumptions, conflict resolution, and explicit human approval are required before treating real-platform values as final.

## BitLesson Delta

Action: none
Lesson ID(s): NONE
Notes: No project bitlesson entries were available; no reusable lesson was added.
