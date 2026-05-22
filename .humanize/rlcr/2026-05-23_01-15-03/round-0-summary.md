# Round 0 Summary

## What Was Implemented

- Built the runnable RVV profiling workflow described by `docs/plan.md`: LLVM-facing schema extraction, synthetic two-pipe timing model, zero-cost timestamp marker semantics, assembly generation, experiment runner, analyzer, parameter search, calibration gate, and replayable Humanize2-style workflow capture.
- Generated and normalized the 10-instruction `SEW=e32`, `LMUL={m1,m2,m4}` experiment suite. The final suite contains 377 trace-producing experiments and records one profile directory per instruction plus common processor metadata.
- Added explicit mode separation between `synthetic_calibration` and `real_platform_profile`: synthetic mode may compare inferred values against configured golden values, while real-platform mode intentionally cannot pass on golden equality.
- After synthetic calibration matched, created an isolated LLVM `llvmorg-22.1.3` worktree and implemented the RISC-V `YuShuXin` schedule model plus focused CodeGen and `llvm-mca` tests. LLVM implementation commit: `16b310c4d2525d193352b729e3e1a84164886cb7`.

## Files Changed

- Profile workflow scripts and generated artifacts were completed in prior Round 0 commits:
  - `scripts/check_env.py`
  - `scripts/gen_asm.py`
  - `scripts/run_experiment.py`
  - `scripts/run_suite.py`
  - `scripts/analyze.py`
  - `scripts/search_model.py`
  - `scripts/export_llvm_draft.py`
  - `scripts/check_calibration_gate.py`
  - `experiments/generated/**`
  - `results/common/**`
  - `results/<instruction>/**`
- Added final LLVM implementation evidence:
  - `results/common/llvm_yushuxin_implementation.md`
  - `results/common/agentic_flow/artifacts/worker_outputs/worker-g.md`
- Updated RLCR state artifacts:
  - `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`
  - `.humanize/rlcr/2026-05-23_01-15-03/round-0-summary.md`

## Validation

- `python3 scripts/check_env.py`: passed.
- `python3 scripts/run_experiment.py experiments/generated/t01-vadd-vv-m1 --dry-run --results-root /tmp/profile-inst-latency-final-one-dry`: passed and wrote one dry-run result.
- `python3 scripts/run_suite.py --killcheck --results-root /tmp/profile-inst-latency-final-killcheck`: passed and wrote 30 kill-check traces.
- `python3 scripts/run_suite.py --all --results-root /tmp/profile-inst-latency-final-all`: passed and wrote 377 traces.
- `find /tmp/profile-inst-latency-final-all -path '*/trace.json' | wc -l`: reported `377`.
- `python3 scripts/analyze.py --all --root /tmp/profile-inst-latency-final-all --aggregate /tmp/profile-inst-latency-final-quality.md`: passed and wrote aggregate analysis plus profile updates under the temporary result root.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile`: failed as expected because real-platform mode has no golden-value exit condition.
- `python3 -m py_compile scripts/*.py`: passed.
- LLVM worktree verification:
  - `/home/zhaosiying/codebase/compiler/build_ysx_host_llvm/bin/llvm-tblgen -I llvm/include -I llvm/lib/Target/RISCV -gen-subtarget llvm/lib/Target/RISCV/RISCV.td -o /tmp/yushuxin-RISCVGenSubtargetInfo.inc`: passed.
  - `cmake -G Ninja -S llvm -B /tmp/yushuxin-llvm-build -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD=RISCV -DLLVM_ENABLE_PROJECTS= -DLLVM_INCLUDE_TESTS=ON -DLLVM_INCLUDE_BENCHMARKS=OFF -DLLVM_BUILD_TESTS=OFF -DLLVM_BUILD_EXAMPLES=OFF`: passed.
  - `ninja -C /tmp/yushuxin-llvm-build llc llvm-mca FileCheck`: passed.
  - Focused `llvm-mca` test for `llvm/test/tools/llvm-mca/RISCV/YuShuXin/rvv-e32-profiled.s`: passed.
  - Focused `llc -verify-machineinstrs` CodeGen test for `llvm/test/CodeGen/RISCV/yushuxin-rvv-codegen.ll`: passed.
  - `git diff --check` in the LLVM worktree: passed before commit.

## Remaining Items

- No blocking Round 0 items remain for the synthetic calibration path.
- Real Paladin/platform profiling remains intentionally gated: it must stop on coverage, stability, confidence, documented assumptions, and explicit human approval, not on golden equality.
- The gem5/real-platform path is represented in the replay and gating artifacts, but this round used the synthetic cmodel calibration mode to validate the agentic flow and LLVM implementation handoff.

## BitLesson Delta

Action: none
Lesson ID(s): NONE
Notes: External bitlesson selector was unsafe under active hooks; no project entries existed, no reusable lesson added.
