# Goal Tracker

<!--
This file tracks the ultimate goal, acceptance criteria, and plan evolution.
It prevents goal drift by maintaining a persistent anchor across all rounds.

RULES:
- IMMUTABLE SECTION: Do not modify after initialization
- MUTABLE SECTION: Update each round, but document all changes
- Every task must be in one of: Active, Completed, or Deferred
- Deferred items require explicit justification
-->

## IMMUTABLE SECTION
<!-- Do not modify after initialization -->

### Ultimate Goal
Build and validate a reproducible, Humanize2-captured RVV instruction latency profiling workflow that can run a gem5 MinorCPU synthetic calibration flow, infer LLVM-aligned scheduling data for 10 non-memory RVV instruction families, distinguish synthetic golden calibration from real-platform profiling, and only after calibrated agreement implement a gated LLVM 22.1.3 RISC-V `YuShuXin` CPU schedule model in an isolated worktree.

Source plan: docs/plan.md

### Acceptance Criteria
<!-- Each criterion must be independently verifiable -->
<!-- Claude must extract or define these in Round 0 -->


- AC-1: The plan is executable from an empty context and identifies exact phases, files, and verification commands.
- AC-2: LLVM is not modified in the first platform-first phase.
- AC-3: gem5 MinorCPU is the first simulator baseline, with an explicit RVV kill-check and fallback candidate-comparison path.
- AC-4: The first instruction set has 10 non-memory RVV instructions spanning distinct schedule families.
- AC-5: First matrix uses `SEW=e32` and `LMUL={m1,m2,m4}`.
- AC-6: Timestamp markers are zero-cost simulator annotations and do not occupy issue bandwidth.
- AC-7: Results are recorded under `results/common/` and one folder per instruction.
- AC-8: Profiles record LLVM-facing fields first and hardware interpretation fields second.
- AC-9: Analysis uses rule inference plus parameter search consistency checks.
- AC-10: Synthetic configured values are compared against inferred values and mismatches are reported.
- AC-11: Future implementation runs through Humanize RLCR with the main agent coordinating and workers isolated from RLCR state.
- AC-12: Implementation continuously records Humanize2-style prompts, tool calls, boards, artifacts, events, decisions, and control flow under `results/common/agentic_flow/`.
- AC-13: The final workflow can be replayed from `results/common/agentic_flow/replay.md` and a draft Humanize2 cartridge without relying on the original chat transcript.
- AC-14: Synthetic cmodel mode distinguishes golden-value calibration from real-platform profiling and records the active mode in results and agentic-flow state.
- AC-15: The `YuShuXin` LLVM 22.1.3 schedule-model implementation starts only after synthetic calibration matches all claimed cmodel ground-truth fields.
- AC-16: Real Paladin/platform profiling never uses golden equality as an exit condition; it stops on coverage, stability, confidence, documented assumptions, and explicit human approval before LLVM implementation.
- AC-17: The LLVM implementation is created in an isolated `llvmorg-22.1.3` worktree and includes RISC-V backend model changes plus focused CodeGen/llvm-mca tests for `-mcpu=YuShuXin`.

## Open Risks

---

## MUTABLE SECTION
<!-- Update each round with justification for changes -->

### Plan Version: 1 (Updated: Round 0)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | - | - |
| 0 | Completed synthetic profiling workflow, replay capture, and gated LLVM 22.1.3 YuShuXin implementation. | Round 0 review required replacing scaffold-only artifacts with runnable generation, analysis, calibration, and LLVM evidence. | AC-1 through AC-17 verified for the synthetic calibration path; real-platform path remains gated by confidence and human approval. |

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| T0 Repository and toolchain bootstrap | AC-1, AC-3 | completed | coding | claude | Environment gate and path config verified with `python3 scripts/check_env.py`. |
| T1 LLVM read-only schedule field extractor | AC-2, AC-4, AC-8 | completed | coding | claude | LLVM field map, schedule family mapping, and 10-instruction schema recorded under `results/common/`. |
| T2 gem5 RVV kill-check and fallback comparison path | AC-3, AC-4, AC-5 | completed | coding | claude | Kill-check path verified through `python3 scripts/run_suite.py --killcheck`; fallback path preserved in plan/replay. |
| T3 Zero-cost timestamp marker and trace schema | AC-6 | completed | coding | claude | Trace schema records zero-cost marker semantics; dry-run and suite traces verified. |
| T4 Synthetic two-pipe timing model and assembly generator | AC-3, AC-5, AC-7 | completed | coding | claude | Generated 377 experiments covering 10 instructions and e32/m1,m2,m4 matrix. |
| T5 Runner, analyzer, parameter search, and mismatch gate | AC-7, AC-8, AC-9, AC-10, AC-14, AC-16 | completed | coding | claude | Full suite, analyzer, parameter search, synthetic PASS gate, and real-platform FAIL gate verified. |
| T6 Humanize2 primitive capture and replay cartridge | AC-11, AC-12, AC-13 | completed | coding | claude | Replay, cartridge, worker outputs, and LLVM evidence are recorded under `results/common/agentic_flow/`. |
| T7 LLVM 22.1.3 YuShuXin schedule-model implementation | AC-15, AC-17 | completed | coding | claude | LLVM worktree commit `16b310c4d2525d193352b729e3e1a84164886cb7`; `llvm-mca` and `llc` focused tests passed. |
| T8 LLVM model draft export and mapping evidence | AC-8, AC-10, AC-15 | completed | coding | claude | `scripts/export_llvm_draft.py` and LLVM implementation evidence recorded. |

### Completed and Verified
<!-- Only move tasks here after Codex verification -->
| AC | Task | Completed Round | Verified Round | Evidence |
|----|------|-----------------|----------------|----------|
| AC-1, AC-3 | T0 Repository and toolchain bootstrap | 0 | 0 | `python3 scripts/check_env.py` passed; config paths verified. |
| AC-2, AC-4, AC-8 | T1 LLVM schedule field extraction | 0 | 0 | `results/common/llvm_field_map.yaml`, 10 instruction profile folders, and LLVM source references recorded. |
| AC-3, AC-4, AC-5 | T2 RVV kill-check path | 0 | 0 | `python3 scripts/run_suite.py --killcheck --results-root /tmp/profile-inst-latency-final-killcheck` wrote 30 traces. |
| AC-6 | T3 Timestamp marker schema | 0 | 0 | `python3 scripts/run_experiment.py experiments/generated/t01-vadd-vv-m1 --dry-run --results-root /tmp/profile-inst-latency-final-one-dry` passed. |
| AC-3, AC-5, AC-7 | T4 Synthetic timing model and assembly generation | 0 | 0 | `python3 scripts/gen_asm.py suite` generated 377 experiments; `python3 scripts/run_suite.py --all --results-root /tmp/profile-inst-latency-final-all` wrote 377 traces. |
| AC-7, AC-8, AC-9, AC-10, AC-14, AC-16 | T5 Analyzer, search, and gates | 0 | 0 | `python3 scripts/analyze.py --all --root /tmp/profile-inst-latency-final-all --aggregate /tmp/profile-inst-latency-final-quality.md`; `python3 scripts/search_model.py --profile results --format json`; synthetic gate PASS; real-platform gate FAIL as expected. |
| AC-11, AC-12, AC-13 | T6 Humanize2 replay capture | 0 | 0 | `results/common/agentic_flow/replay.md`, cartridge, artifacts, worker outputs, and this tracker updated. |
| AC-15, AC-17 | T7 LLVM YuShuXin implementation | 0 | 0 | LLVM commit `16b310c4d2525d193352b729e3e1a84164886cb7`; `ninja -C /tmp/yushuxin-llvm-build llc llvm-mca FileCheck`; focused `llvm-mca` and `llc -verify-machineinstrs` tests passed. |
| AC-8, AC-10, AC-15 | T8 LLVM model draft export | 0 | 0 | `results/common/llvm_model_draft.td`, `results/common/llvm_yushuxin_implementation.md`, and profile YAML evidence recorded. |

### Explicitly Deferred
<!-- Items here require strong justification -->
| Task | Original AC | Deferred Since | Justification | When to Reconsider |
|------|-------------|----------------|---------------|-------------------|

### Open Issues
<!-- Issues discovered during implementation -->
| Issue | Discovered Round | Blocking AC | Resolution Path |
|-------|-----------------|-------------|-----------------|
| None open after Round 0 fixes. | Round 0 | - | Synthetic calibration path passes; real-platform profiling remains intentionally gated by confidence and explicit human approval rather than golden equality. |
