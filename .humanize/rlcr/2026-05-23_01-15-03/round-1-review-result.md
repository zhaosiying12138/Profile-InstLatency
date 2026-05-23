# Round 1 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Round 1 fixed several previously valid review findings. The current checkout has two complete real gem5 repetitions, mode/backend-filtered real-platform search artifacts, `profile.real_platform.yaml` sidecars for all 10 instructions, a machine-readable field-status sidecar, marker-contract inventory, and a real-platform gate that fails closed on field-status risks. This is real progress, but it is not completion. The original plan still requires candidate timing-model resimulation, and the current real-platform evidence still reports 118 unresolved LLVM-facing field risks plus missing explicit human approval.

## Findings

### HIGH 1. The planned candidate timing-model simulator is still missing

The plan is explicit that parameter search must enumerate `Latency`, `ReleaseAtCycles`, pipe assignment, `NumMicroOps`, and `SingleIssue`, re-simulate expected template timings, and choose the minimal explaining parameter set (`docs/plan.md:422-425`). Phase 7 also requires parameter search to verify consistency and write field confidence/evidence into YAML (`docs/plan.md:586-608`).

The current implementation is still a set of independent field equations rather than a shared simulator:

- `Latency` is filtered directly by `delta == (iterations - 1) * Latency` for T11 (`scripts/search_model.py:694-719`).
- `ReleaseAtCycles` is filtered directly by `delta == (iterations - 1) * ReleaseAtCycles` for T10 (`scripts/search_model.py:722-745`).
- T20 only interprets pair deltas after release values are uniquely known; it does not enumerate pipe assignments through a common timing model (`scripts/search_model.py:760-825`).
- T21 only interprets `NumMicroOps` and `SingleIssue` after release is unique, using an ad hoc scalar-pair formula (`scripts/search_model.py:873-960`).
- `TimingCandidate` and `CandidateSearchResult` exist as data classes, but there is no shared template-body resimulation path using them (`scripts/search_model.py:93-107`).

The generated evidence confirms the gap: `results/common/experiment_quality.md:10-13` reports 118 unresolved LLVM field-status risks, and the regenerated search has 44 conflicts plus 74 insufficient-evidence rows. This keeps AC-9 incomplete.

### HIGH 2. The real-platform flow is not approval-ready and cannot be called complete

AC-16 requires the real-platform path to stop on coverage, stability, confidence, documented assumptions, and explicit human approval (`docs/plan.md:734-749`, `docs/plan.md:1058`). Coverage and repeatability are now good: `results/common/experiment_quality.md:31-41` reports 178/178 required groups, 3221 stable repeat groups, and 0 unstable groups.

The remaining stop conditions are not met:

- `results/common/experiment_quality.md:3-13` says `Gate status: NOT_READY`, confidence is `unresolved_llvm_field_status`, approval is absent, and field-status unresolved risks total 118.
- `scripts/check_calibration_gate.py:684-717` correctly fails unresolved field-status risks unless they are accepted by a valid approval path.
- Re-run evidence: `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` exits 1 with missing `Gate status: PASS`, missing machine-readable approval, and 118 unresolved field-status risks.

Failing closed is the right behavior. It is also proof that the original plan is not fully complete under this review prompt.

### MEDIUM 3. The real-platform search summary contradicts the corrected interval equations

Claude's summary says T10/T11 were corrected from `iterations * field` to `(iterations - 1) * field`, and the code/evidence strings do use that interval rule (`scripts/search_model.py:706-708`, `scripts/search_model.py:735-737`). However, the generated real-platform search summary still documents the old assumptions:

- `results/common/search_model_real_platform_summary.md:18` says `delta_cycles == iterations * ReleaseAtCycles`.
- `results/common/search_model_real_platform_summary.md:19` says `delta_cycles == iterations * Latency`.

That artifact is part of the replayable evidence trail and should not contradict the actual search logic. Regenerate it after fixing `global_assumptions` in `scripts/search_model.py:1164-1169`.

## Goal Alignment Summary

ACs: 15/17 addressed | Forgotten items: 1 | Unjustified deferrals: 1

- AC-1 through AC-8, AC-10 through AC-15, and AC-17 have reviewable evidence.
- AC-9 remains incomplete because candidate timing-model resimulation and minimal candidate selection are still not implemented.
- AC-16 remains incomplete because the real-platform gate is still `NOT_READY` due 118 unresolved field risks and absent explicit human approval.
- Forgotten item: the generated real-platform search summary still carries stale `iterations * field` equations after the interval correction.
- Unjustified deferral: the shared candidate timing-model simulator was admitted as pending. The review prompt requires it to be completed, not deferred.

## Goal Tracker Update Handling

Claude's update request was partially approved and applied to the mutable section of `goal-tracker.md`.

- Approved: real gem5 repeat coverage is recorded as verified evidence. `results/r01` and `results/r02` contain 6442 trace files, 178/178 required real gem5 groups are covered, and repeatability is 3221 stable groups with 0 unstable groups.
- Approved: mode-isolated real-platform search/profile artifacts are recorded as completed evidence. The focused search uses 6472 filtered `real_platform_profile`/`gem5_minor` traces and produces `search_model_real_platform.json`, `real_platform_field_status.json`, and 10 `profile.real_platform.yaml` files.
- Approved: field-status and marker-contract gate wiring is recorded as completed evidence. The real-platform gate now fails on unresolved field risks and missing approval.
- Rejected: T9/T10/T11 were not moved to fully completed task status. T9 still lacks an approval-ready report, T10 still lacks the shared candidate simulator, and T11 still has a blocked gate outcome.
- Updated: Plan Version is now 5, the Round 1 review row reflects current HEAD rather than the stale pre-fix review, and open issues now focus on the remaining candidate simulator, unresolved field risks, missing approval, and stale summary equations.

## Directive Implementation Plan

Claude must execute this plan before requesting another completion review:

1. Replace `search_model.py`'s independent field filters with a shared candidate timing-model simulator. The simulator must enumerate candidate tuples per instruction/LMUL over `Latency`, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue`, then replay the actual T10/T11/T12/T20/T21/T30 template bodies using the plan assumptions: in-order issue, issue width 2, no ROB, zero-cost markers, scalar companion issue cost 1, and two vector resources.
2. Use the corrected interval contract everywhere: marker deltas around N repeated operations use `N - 1` intervals for T10/T11 unless the template metadata proves a different marker placement. Update `global_assumptions` and regenerate the markdown summaries so documentation and evidence agree.
3. Make T20 pipe/resource classification part of the candidate simulation. Candidate pipe assignments must be eliminated by pairwise timing, not by synthetic labels or by post-hoc relation strings alone.
4. Make T21 `NumMicroOps` and `SingleIssue` checks part of the same candidate simulation. Do not require `ReleaseAtCycles` to be uniquely solved by a separate pre-pass before evaluating issue-field candidates.
5. Use T12 only through the shared simulator. If the current templates cannot identify bypass/read-advance behavior, emit a non-identifiable status with a concrete follow-up experiment rather than treating it as solved.
6. Select the minimal candidate set explaining all real observations within the configured tolerance. If no candidate exists, emit `conflict` with the failing observations. If multiple candidates remain, emit `insufficient_evidence` with a specific follow-up template and operands.
7. Regenerate `results/common/search_model_real_platform.json`, `results/common/search_model_real_platform_summary.md`, `results/common/real_platform_field_status.json`, all 10 `profile.real_platform.yaml` sidecars, `results/common/real_platform_inventory.json`, and `results/common/experiment_quality.md`.
8. Keep the real-platform gate fail-closed. Do not create a human approval artifact unless the user explicitly approves the exact remaining risk set. If risks remain, the approval artifact must identify accepted risk IDs and tie approval to both inventory and field-status hashes.
9. Re-run verification:
   - `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py`
   - `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`
   - `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search.json --format json`
   - `python3 -m json.tool /tmp/profile-inst-latency-real-search.json`
   - `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`
   - `find results/r01 results/r02 -name trace.json | wc -l`

Do not output `COMPLETE` unless all original plan tasks are done, the candidate simulator exists, all real-platform field risks are resolved or explicitly approved by the user, the real-platform gate passes, and no active/deferred plan work remains.

## Reviewer Verification Commands

- `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py`: passed.
- `python3 -m json.tool results/common/real_platform_inventory.json`, `results/common/real_platform_field_status.json`, and `results/common/search_model_real_platform.json`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed as expected on missing `Gate status: PASS`, missing machine-readable approval, and 118 unresolved field-status risks.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search.json --format json`: passed and used 6472 filtered real gem5 traces.
- `/tmp/profile-inst-latency-real-search.json` status counts: 22 `Latency` conflicts, 22 `ReleaseAtCycles` conflicts, 30 `ProcResource` insufficient-evidence rows, 22 `NumMicroOps` insufficient-evidence rows, 22 `SingleIssue` insufficient-evidence rows, and 32 inferred rows.
- `find results/r01 results/r02 -name trace.json | wc -l`: `6442`.

REQUEST CHANGES
