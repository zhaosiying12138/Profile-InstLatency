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

### Plan Version: 2 (Updated: Round 1)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | - | - |
| 0 | Completed synthetic profiling workflow, replay capture, and gated LLVM 22.1.3 YuShuXin implementation. | Round 0 review required replacing scaffold-only artifacts with runnable generation, analysis, calibration, and LLVM evidence. | AC-1 through AC-17 verified for the synthetic calibration path; real-platform path remains gated by confidence and human approval. |
| 0-review | Completion claim rejected by Codex review. | Fresh review found the kill-check and all suite traces are synthetic cmodel outputs, generated assembly still contains assembler-illegal `TIMESTAMP_MARK` pseudo-ops, analyzer/search copy configured synthetic metadata rather than inferring from raw marker evidence, and Humanize2 state is stale. | AC-3, AC-6, AC-9, AC-10, AC-12, AC-13, AC-14, AC-15, AC-16, and AC-17 remain blocked or invalidly gated. |
| 1 | Review findings corrected and rerun end-to-end. | Marker pseudo-ops are lowered to assembler-legal zero-cost labels; gem5 MinorCPU T01 kill-check passes; analyzer infers claimed fields from raw marker deltas; synthetic gate passes; LLVM mca checks now cover all 30 profiled rows. | AC-1 through AC-17 are verified for the synthetic calibration branch; AC-16 remains the required gate for future real-platform expansion. |

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| T0 Repository and toolchain bootstrap | AC-1, AC-3 | completed | coding | claude | Environment gate and path config verified with `python3 scripts/check_env.py`. |
| T1 LLVM read-only schedule field extractor | AC-2, AC-4, AC-8 | completed | coding | claude | LLVM field map, schedule family mapping, and 10-instruction schema recorded under `results/common/`. |
| T2 gem5 RVV kill-check and fallback comparison path | AC-3, AC-4, AC-5 | completed | coding | claude | `python3 scripts/run_suite.py --killcheck --backend gem5_minor --results-root results` passed for 10 instructions x 3 LMUL; fallback doc updated. |
| T3 Zero-cost timestamp marker and trace schema | AC-6 | completed | coding | claude | `TIMESTAMP_MARK` is lowered to zero-cost labels; gem5 traces recover marker cycles from symbol PCs and Exec logs. |
| T4 Synthetic two-pipe timing model and assembly generator | AC-3, AC-5, AC-7 | completed | coding | claude | Suite regenerated with 3221 experiments including multiple T10/T11 stream lengths and T12 K=0..40 sweeps. |
| T5 Runner, analyzer, parameter search, and mismatch gate | AC-7, AC-8, AC-9, AC-10, AC-14, AC-16 | completed | coding | claude | Analyzer claims latency/release/resource fields from raw marker deltas; synthetic gate passes; real gate fails closed without human approval. |
| T6 Humanize2 primitive capture and replay cartridge | AC-11, AC-12, AC-13 | completed | coding | claude | Boards, events, replay notes, cartridge, tool-call artifacts, and coordinator Round 1 output updated under `results/common/agentic_flow/`. |
| T7 LLVM 22.1.3 YuShuXin schedule-model implementation | AC-15, AC-17 | completed | coding | claude | LLVM worktree has schedule-model commit plus strengthened mca test commit; focused mca/codegen tests pass. |
| T8 LLVM model draft export and mapping evidence | AC-8, AC-10, AC-15 | completed | coding | claude | Profiles, mismatch report, search output, and LLVM evidence are regenerated after non-circular synthetic calibration. |

### Completed and Verified
<!-- Only move tasks here after Codex verification -->
| AC | Task | Completed Round | Verified Round | Evidence |
|----|------|-----------------|----------------|----------|
| AC-1, AC-3 | T0 Repository and toolchain bootstrap | 0 | 0 | `python3 scripts/check_env.py` passed; config paths verified. |
| AC-2, AC-4, AC-8 | T1 LLVM schedule field extraction | 0 | 0 | `results/common/llvm_field_map.yaml`, 10 instruction profile folders, and LLVM source references recorded. |
| AC-3, AC-4, AC-5 | T2 gem5 RVV kill-check | 1 | 1 | 30 `results/common/experiments/t01-*/trace.json` files with `backend: gem5_minor` and `mode: real_platform_profile`. |
| AC-6 | T3 zero-cost marker path | 1 | 1 | Adjacent marker baseline and generated marker metadata use zero-cost label markers; `TIMESTAMP_MARK` no longer appears in generated assembly. |
| AC-5, AC-7, AC-9 | T4 experiment matrix | 1 | 1 | `python3 scripts/gen_asm.py suite --output-root experiments/generated` produced 3221 suite entries. |
| AC-7, AC-8, AC-9, AC-10, AC-14, AC-16 | T5 analyzer/search/gates | 1 | 1 | `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results --mismatch-report results/common/mismatch_report.md` passed; real-platform gate failed closed as expected. |
| AC-11, AC-12, AC-13 | T6 Humanize2 capture | 1 | 1 | `results/common/agentic_flow/replay.md`, boards, events, cartridge, and coordinator verification artifacts updated. |
| AC-15, AC-17 | T7 LLVM YuShuXin implementation | 1 | 1 | LLVM commits `16b310c4d252` and `13a8f69179f0`; focused llvm-mca and llc FileCheck commands passed. |
| AC-8, AC-10, AC-15 | T8 LLVM mapping evidence | 1 | 1 | `results/common/llvm_yushuxin_implementation.md`, profiles, and mismatch report regenerated from corrected inference. |

### Explicitly Deferred
<!-- Items here require strong justification -->
| Task | Original AC | Deferred Since | Justification | When to Reconsider |
|------|-------------|----------------|---------------|-------------------|

### Open Issues
<!-- Issues discovered during implementation -->
| Issue | Discovered Round | Blocking AC | Resolution Path |
|-------|-----------------|-------------|-----------------|
| Full real-platform timing suite is not complete; only T01 gem5 kill-check has real coverage. | Round 1 | AC-16 future expansion | Keep `real_platform_profile` gate NOT_READY until T10/T11/T12/T20/T30 have repeated real traces, confidence review, and human approval. |
