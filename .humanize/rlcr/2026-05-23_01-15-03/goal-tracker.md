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

### Plan Version: 7 (Updated: Round 3 review)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | - | - |
| 0 | Completed synthetic profiling workflow, replay capture, and gated LLVM 22.1.3 YuShuXin implementation. | Round 0 review required replacing scaffold-only artifacts with runnable generation, analysis, calibration, and LLVM evidence. | AC-1 through AC-17 verified for the synthetic calibration path; real-platform path remains gated by confidence and human approval. |
| 0-review | Completion claim rejected by Codex review. | Fresh review found the kill-check and all suite traces are synthetic cmodel outputs, generated assembly still contains assembler-illegal `TIMESTAMP_MARK` pseudo-ops, analyzer/search copy configured synthetic metadata rather than inferring from raw marker evidence, and Humanize2 state is stale. | AC-3, AC-6, AC-9, AC-10, AC-12, AC-13, AC-14, AC-15, AC-16, and AC-17 remain blocked or invalidly gated. |
| 1 | Review findings corrected and rerun end-to-end. | Marker pseudo-ops are lowered to assembler-legal zero-cost labels; gem5 MinorCPU T01 kill-check passes; analyzer infers claimed fields from raw marker deltas; synthetic gate passes; LLVM mca checks now cover all 30 profiled rows. | AC-1 through AC-17 are verified for the synthetic calibration branch; AC-16 remains the required gate for future real-platform expansion. |
| 0-review-recheck | Completion claim rejected by fresh Codex review. | The corrected state satisfies the synthetic calibration branch and gem5 T01 kill-check, but the original plan still requires completing non-deferred real-platform coverage/gating and a parameter search that enumerates candidate timing parameters against raw observations. | AC-9 and AC-16 remain incomplete; AC-6 remains weak until the marker baseline is checked as real gem5 evidence rather than only synthetic/label-PC inference. |
| 1-review | Round 1 completion request partially rejected after rechecking current HEAD. | Repeated gem5 traces, mode-isolated real-platform search artifacts, real-platform profile sidecars, field-status inventory, and marker-contract gate wiring now exist. Completion is still blocked because the planned shared candidate timing-model simulator is incomplete, 118 LLVM-facing real-platform field risks remain unresolved, and explicit human approval is absent. | AC-9 remains incomplete; AC-16 remains blocked by unresolved field-status risks and missing approval. |
| 2-review | Round 2 completion request rejected after reviewing the candidate-search implementation. | A shared candidate tuple path and regenerated artifacts now exist, the stale search-summary interval equations are fixed, and blocking field-status risks dropped from 118 to 5. Completion remains blocked because non-chainable T11 placeholders are still used as latency evidence, T20 pair timing is skipped instead of eliminating ProcResource candidates, 29 ProcResource rows are non-identifiable, `vcpop_m` LMUL `m4` still has 5 conflicts, and explicit human approval is absent. | AC-9 remains incomplete; AC-16 remains blocked by unresolved real-platform confidence/approval requirements. |
| 3-review | Round 3 completion request rejected after reviewing expanded diagnostics. | Generated and checked-in real T20 pair-count sweeps now exist, non-chainable T11 rows are no longer claimed as latency evidence, and the `vcpop_m` LMUL `m4` conflicts were conservatively converted to `non_identifiable` rows rather than guessed affine LLVM fields. Completion remains blocked because T20 observations are still skipped by the shared candidate simulator, T12 bypass/read-advance latency modeling is not implemented, 48 LLVM-facing rows remain non-identifiable, and explicit human approval is absent. | AC-9 remains incomplete; AC-16 remains blocked by missing approval and unresolved non-identifiable real-platform fields. |

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
| T9 Real gem5 timing suite and approval-ready quality report | AC-3, AC-6, AC-16 | needs_changes | coding | claude | Repeated real gem5 coverage is verified under `results/r01` and `results/r02` with 7190 checked-in trace files; `experiment_quality.md` reports 178/178 required groups, 3595/3595 stable repeat groups, marker contract PASS, and 0 conflict rows. The quality report remains NOT_READY because 48 LLVM-facing fields are non-identifiable and explicit human approval is absent. |
| T10 Raw-observation parameter search | AC-9, AC-10 | needs_changes | coding | claude | Round 3 corrected non-chainable T11 evidence routing and records T20 startup+slope groups, but the planned simulator is still incomplete: T20 observations are skipped instead of constraining candidate tuples, 30 ProcResource rows remain non-identifiable, and T12 bypass/read-advance latency modeling is not implemented for 15 non-chainable latency rows. |
| T11 Real-platform gate enforcement | AC-16 | needs_changes | coding | claude | Gate validates trace inventory, repeat coverage, marker contract, field-status risks, and approval hashes. It correctly fails closed on missing `Gate status: PASS` plus missing machine-readable human approval under `results/common`; keep active until an explicit approval artifact is provided and the real-platform gate passes. |

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
| AC-3, AC-6, AC-16 | T9 real gem5 repeat coverage and marker-contract inventory | 1 | 1-review | `results/r01` and `results/r02` contain 6442 trace files; `results/common/experiment_quality.md` reports 178/178 required real gem5 groups, 3221 stable repeat groups, 0 unstable groups, and marker contract evidence is present in `results/common/real_platform_inventory.json`. |
| AC-8, AC-14, AC-16 | T10 mode-isolated real-platform search/profile artifacts | 1 | 1-review | `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search.json --format json` used 6472 filtered real gem5 traces and regenerated `results/common/search_model_real_platform.json`, `results/common/real_platform_field_status.json`, and 10 `profile.real_platform.yaml` sidecars. |
| AC-16 | T11 field-status and marker-contract gate wiring | 1 | 1-review | Gate wiring is verified fail-closed; current Round 2 evidence fails on missing approval and 5 unresolved real-platform LLVM field-status conflicts from `results/common/real_platform_inventory.json`. |

### Explicitly Deferred
<!-- Items here require strong justification -->
| Task | Original AC | Deferred Since | Justification | When to Reconsider |
|------|-------------|----------------|---------------|-------------------|

### Open Issues
<!-- Issues discovered during implementation -->
| Issue | Discovered Round | Blocking AC | Resolution Path |
|-------|-----------------|-------------|-----------------|
| T12 latency modeling remains absent for non-chainable instruction results. | Round 3 review | AC-9, AC-16 | Implement a producer-result-to-consumer readiness model for `T12_CONSUMER_RAW_GAP`, including scalar-result consumers such as `vcpop_m`, and regenerate search/profile/field-status/inventory/quality artifacts so non-chainable latency rows are inferred or explicitly risk-accepted. |
| T20 resource classification is recorded but still not enforced by the shared candidate simulator. | Round 3 review | AC-9, AC-16 | Wire `T20_PAIRWISE_PIPE_CLASSIFICATION` into candidate checking using the generated multi-count sweeps, two-pipe allocation, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue`; eliminate or justify the 30 non-identifiable ProcResource rows. |
| `vcpop_m` LMUL `m4` is no longer a conflict, but its non-affine stream behavior remains non-identifiable. | Round 3 review | AC-9, AC-16 | Keep the conservative non-identifiable classification unless an explicit model or human risk acceptance is added; use the focused T10 stream-length/alignment/scalar-destination/source-register sweep to decide whether any LLVM-facing field can be claimed. |
| Explicit real-platform human approval artifact is absent. | Round 1 review | AC-16 | After the field-status report is approval-ready, obtain explicit human approval tied to `real_platform_inventory.json` and `real_platform_field_status.json` hashes before allowing the real-platform gate to pass. |
