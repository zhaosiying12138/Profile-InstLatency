# Round 2 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Round 2 made real progress: `HEAD` is now `14bc45c4 Implement real platform candidate search`, the stale real-platform summary equations are fixed, the generated field-status sidecar now reports 5 blocking conflicts instead of 118, and the real-platform gate still fails closed. It is still not complete. The current implementation does not satisfy the original candidate-simulator requirements because it treats non-chainable T11 placeholder streams as latency evidence and skips T20 pair/resource checks instead of using them to eliminate `ProcResource` candidates. The real-platform gate also remains `NOT_READY` with no explicit human approval.

## Findings

### HIGH 1. Non-chainable T11 placeholder bodies are used as real latency evidence

The plan requires `T11`/`T12` to give observable latency and parameter search to validate actual template timings (`docs/plan.md:416-425`, `docs/plan.md:597-608`). The generator explicitly says non-chainable instructions are only placeholder T11 bodies and should prefer T12: `body_t11` emits "documented placeholder; use T12" when `spec.chainable` is false (`scripts/gen_asm.py:675-695`). Several selected instructions are marked non-chainable, including `vmseq_vv`, `vcpop_m`, `viota_m`, `vslideup_vx`, and `vrgather_vv` (`scripts/gen_asm.py:119-157`).

`scripts/search_model.py` ignores that metadata. It builds latency candidate domains from every `T11_SELF_RAW_CHAIN` observation (`scripts/search_model.py:1052-1057`) and labels every T11 body as `startup + (N - 1) * Latency` (`scripts/search_model.py:929-936`). As a result, `vcpop_m` `m1` is reported as an inferred latency with T11 evidence even though the T11 body is not a true RAW chain (`results/vcpop_m/profile.real_platform.yaml:7-21`).

This invalidates a meaningful subset of the exact-fit latency claims and likely contributes to the `vcpop_m` `m4` conflict. Do not treat this as an approved non-identifiability deferral: the search must either model the proper T12 consumer path for non-chainable results or mark those latency rows unresolved with concrete follow-up experiments.

### HIGH 2. T20 ProcResource classification is deferred instead of simulated

The original plan says `T20` produces pipe class/resource group candidates and Phase 7 must classify pipe affinity using pairwise throughput (`docs/plan.md:416-425`, `docs/plan.md:597-602`). The Round 1 directive was even more explicit: "Make T20 pipe/resource classification part of the candidate simulation" (`round-2-prompt.md:95-100`).

The current candidate path does the opposite. `expected_delta_for_observation` returns `None` for every `T20_PAIRWISE_PIPE_CLASSIFICATION` observation and records it as non-identifiable (`scripts/search_model.py:939-946`). `candidate_field_result` then converts surviving multi-resource candidates into `non_identifiable` and tells a future round to add a T20 sweep or pipe-label trace (`scripts/search_model.py:1207-1218`). The generated status confirms the gap: 29 `ProcResource` rows are `non_identifiable`, and each one carries that same future-work reason (`results/common/real_platform_field_status.json`; summary at `results/common/experiment_quality.md:3283-3288`). A representative profile shows all three resource candidates still alive for `vadd_vv m1` (`results/vadd_vv/profile.real_platform.yaml:37-44`).

This keeps AC-9 incomplete and makes the real-platform confidence report weaker than Claude's summary implies. "Remaining 5 conflicts" is only the blocking-count view; it hides that the implementation did not actually infer ProcResource for the other 29 rows.

### HIGH 3. AC-16 remains blocked by conflicts and missing approval

AC-16 requires real-platform profiling to stop on coverage, stability, confidence, documented assumptions, and explicit human approval (`docs/plan.md:734-749`, `docs/plan.md:1058`). The current quality report still says `Gate status: NOT_READY`, `Confidence: unresolved_llvm_field_status`, and `Human approval status: absent` (`results/common/experiment_quality.md:3-13`). The field-status section lists 5 unresolved conflicts, all for `vcpop_m m4` (`results/common/experiment_quality.md:3280-3297`), and the gate fails as expected:

`python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`

failed with missing `Gate status: PASS`, missing machine-readable approval, and 5 unresolved real-platform LLVM field-status conflicts. This fail-closed behavior is correct, but it proves the work is not complete under this review prompt.

### MEDIUM 4. Conflict follow-up is still too generic to satisfy the plan

The plan requires every conflict to have an `analysis.md` explanation and a concrete next experiment proposal (`docs/plan.md:604-608`). The field-status generator uses a generic follow-up string for all conflict/insufficient rows: "Add a focused experiment that separates issue occupancy, pipe identity, and RAW readiness" (`scripts/search_model.py:1748-1751`). The `vcpop_m m4` rows therefore do not name a concrete template, body shape, operand/register policy, or pair-count/gap sweep. That is not enough for a worker to execute accurately.

## Goal Alignment Summary

ACs: 15/17 addressed | Forgotten items: 1 | Unjustified deferrals: 2

- AC-1 through AC-8, AC-10 through AC-15, and AC-17 still have prior reviewable evidence.
- AC-9 remains incomplete: the candidate path exists, but it mishandles non-chainable T11 latency and does not use T20 to eliminate pipe/resource candidates.
- AC-16 remains incomplete: the real-platform gate is `NOT_READY`, 5 field-status conflicts remain, 29 ProcResource rows are non-identifiable, and explicit human approval is absent.
- Forgotten item: the tracker did not previously track the non-chainable T11 latency-evidence bug; it is now added.
- Unjustified deferrals: the proposed future T20 sweep/pipe-label evidence and the `vcpop_m m4` diagnostic experiment are required by the original plan and must be executed, not deferred.

## Goal Tracker Update Handling

Claude's update request was partially approved and applied to the mutable section of `goal-tracker.md`.

- Approved: the stale real-platform search-summary equation issue is resolved; `results/common/search_model_real_platform_summary.md:18-19` now documents `startup + (N - 1) * ReleaseAtCycles` and `startup + (N - 1) * Latency`.
- Approved: the unresolved blocking field-status count is updated from 118 to 5, all scoped to `vcpop_m` LMUL `m4`.
- Rejected: T10 was not moved to completed. The candidate tuple path exists, but T20 is skipped, non-chainable T11 bodies are used as latency evidence, and `vcpop_m m4` still conflicts.
- Kept active: T9 and T11 remain active because the quality report is not approval-ready and the real-platform gate still fails.
- Added open issues: non-chainable latency modeling, 29 non-identifiable ProcResource rows, `vcpop_m m4` conflicts, and missing explicit approval.

## Directive Implementation Plan

Claude must execute this exact plan before requesting another completion review:

1. Fix latency evidence routing in `scripts/search_model.py`. Read the `body.chainable`/instruction metadata from each observation. Use T11 as a hard `Latency` constraint only when the generated body is a real self RAW chain. For non-chainable bodies, remove T11 from latency constraints and drive latency from an explicit T12 consumer-gap model; if the current T12 marker contract cannot identify the field, emit `non_identifiable` or `insufficient_evidence` with a concrete follow-up template instead of `exact_fit`.
2. Implement T20 in the shared simulator. Stop returning `None` for `T20_PAIRWISE_PIPE_CLASSIFICATION`. Add candidate checks that compare observed pair-count slopes against a two-pipe in-order issue model using `Latency`, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue`.
3. Extend the T20 experiment matrix now. Generate T20 pair-count sweeps for each instruction pair and LMUL, at minimum `N=2,3,4` plus any longer count that the register policy supports. Preserve `register_reuse` in metadata and either model its effect or exclude reused cases from hard constraints with an explicit reason.
4. Model flexible pipe allocation correctly. A fixed `pipe0`/`pipe1` pair serializes only when both candidates require the same pipe; different fixed pipes can overlap; `AnyVPipe` candidates must be allocated to an available pipe under issue width 2 instead of being treated as same-resource by default; `SingleIssue` must serialize the pair when applicable.
5. Add targeted `vcpop_m m4` diagnostics. Generate and run focused real-platform experiments that distinguish independent scalar-destination throughput from RAW readiness: T10 with fixed versus rotated scalar destinations, T11 only if a true scalar RAW chain exists, and T12 scalar-consumer gap sweeps for the `vcpop.m` scalar result.
6. Make conflict reporting executable. For every conflict row, write a concrete follow-up entry naming the template ID, instruction, LMUL, pair/consumer instruction if relevant, pair count or gap sweep, and register policy. Update per-experiment `analysis.md` or an equivalent generated analysis artifact so the conflict is not only described in aggregate JSON.
7. Regenerate all real-platform artifacts: `results/common/search_model_real_platform.json`, `results/common/search_model_real_platform_summary.md`, `results/common/real_platform_field_status.json`, all 10 `profile.real_platform.yaml` sidecars, `results/common/real_platform_inventory.json`, and `results/common/experiment_quality.md`.
8. Keep the real-platform gate fail-closed. Do not create a human approval artifact unless the user explicitly approves the exact remaining risk IDs after the report is approval-ready. If any unresolved risk remains, the approval artifact must bind accepted risk IDs to inventory and field-status hashes.
9. Re-run verification:
   - `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py`
   - `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`
   - `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search.json --format json`
   - `python3 -m json.tool /tmp/profile-inst-latency-real-search.json`
   - `python3 -m json.tool results/common/real_platform_inventory.json >/dev/null && python3 -m json.tool results/common/real_platform_field_status.json >/dev/null && python3 -m json.tool results/common/search_model_real_platform.json >/dev/null`
   - `find results/r01 results/r02 -name trace.json | wc -l`
   - `git diff --check`
   - `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`
10. Replace `round-2-summary.md` with a fresh summary covering changed files, verification outputs, remaining risks, and a Goal Tracker Update Request. Commit the implementation with a descriptive message.

Do not output `COMPLETE` unless all original plan tasks are done, T20 resource classification is actually modeled, non-chainable latency evidence is corrected, all real-platform field risks are resolved or explicitly approved by the user, the real-platform gate passes, and no active/deferred work remains.

## Reviewer Verification Commands

- `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 -m json.tool results/common/real_platform_inventory.json`: passed.
- `python3 -m json.tool results/common/real_platform_field_status.json`: passed.
- `python3 -m json.tool results/common/search_model_real_platform.json`: passed.
- `find results/r01 results/r02 -name trace.json | wc -l`: `6442`.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search.json --format json`: passed and wrote `/tmp/profile-inst-latency-real-search.json`.
- `python3 -m json.tool /tmp/profile-inst-latency-real-search.json >/dev/null`: passed.
- `git diff --check`: passed before this review-result/tracker update.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed as expected on missing `Gate status: PASS`, missing machine-readable approval, and 5 unresolved real-platform LLVM field-status conflicts.

REQUEST CHANGES
