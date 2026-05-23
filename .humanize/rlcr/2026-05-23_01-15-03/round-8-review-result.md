# Round 8 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Round 8 did not complete the original plan. Claude accurately recorded that AC-16 remains blocked, but the round only committed a blocked-status summary and left the real-platform gate failing. I also found one additional current-state implementation issue: the machine-readable field-status sidecar says there are zero blocking rows while the gate and quality report correctly treat the 39 `non_identifiable` rows as approval-bound blockers.

## Part 1: Implementation Review

### BLOCKER 1. AC-16 is still incomplete and Round 8 made no gate-progressing change

The original plan requires real-platform profiling to stop only on coverage, stability, confidence, documented assumptions, and explicit human approval before LLVM implementation (`docs/plan.md:1058`). Round 8 admits that no approval artifact was created and that the remaining work is still approval or stronger evidence for 39 `non_identifiable` rows (`round-8-summary.md:4-16`).

Current artifacts confirm the blocker:

- `results/common/experiment_quality.md:3-13` reports `Gate status: NOT_READY`, `Confidence: unresolved_llvm_field_status`, absent human approval, and 39 unresolved field-status risks.
- `results/common/experiment_quality.md:3641-3646` lists failed checks `required_llvm_field_status_clean_or_accepted` and `explicit_human_approval`.
- `results/common/experiment_quality.md:3657-3660` reports 111 inferred rows and 39 `non_identifiable` rows.
- `results/common/experiment_quality.md:3726-3729` says the approval artifact is absent and the gate cannot pass without clean evidence or per-risk acceptance.
- `results/common/real_platform_risk_acceptance_request.json:6-14` is still explicitly pending, not approved, not a gate input, and not consumed by the gate.
- `find results/common -maxdepth 1 -iname '*approval*' -print` produced no files.

Reviewer reproduction:

```text
$ python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
FAIL: real_platform_profile gate did not pass using results/common/experiment_quality.md
- quality report must contain exact line `Gate status: PASS`
- missing machine-readable human approval file under results/common
- results/common/real_platform_inventory.json: unresolved real-platform LLVM field-status risks=39 status_counts={"non_identifiable": 39}
```

Required completion plan:

1. Treat the current state as not approved. Do not create `results/common/human_approval.json` unless the human owner supplies explicit approval for the current hashes, an approver identity, and accepted risk scope.
2. Fix BLOCKER 2 below before presenting any approval packet, because the current sidecar summary is internally contradictory.
3. If explicit approval is supplied, create only the gate-discoverable `results/common/human_approval.json` with `status: approved`, `approved_by`, current `inventory_sha256`, current `real_platform_field_status_sha256`, and `accepted_risk_ids` covering the exact unresolved risks. Regenerate inventory/quality artifacts and require `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` to pass.
4. If explicit approval is not supplied at the start of the next round, execute the stronger-evidence path instead of ending another handoff-only round:
   - Add targeted T20 resource-disambiguation coverage using the existing `T20_PAIRWISE_PIPE_CLASSIFICATION` template ID. Generate both subject-anchor and anchor-subject pair-count sweeps for every ProcResource row still marked `non_identifiable`, keep `register_reuse=false`, and record the discriminator metadata in each `experiment.yaml`.
   - Update `scripts/search_model.py` so T20 constraints are solved as one global resource-assignment problem across all instruction/LMUL rows, using startup-free pair slopes plus already-inferred release values. A ProcResource row may become `inferred` only when the global solution leaves one LLVM resource/group value; otherwise it must remain `non_identifiable`.
   - Add T12 readiness modeling for the six upper-bound-only latency rows (`vcpop_m` m1/m2/m4, `viota_m` m4, `vrgather_vv` m4, `vslideup_vx` m4). The model must distinguish exact latency from a conservative upper bound; do not turn `Latency <= N` into an exact value without a no-stall transition and post-transition plateau.
   - Add a focused vcpop.m m4 stream model or experiment family for the non-affine rows (`ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, `SingleIssue`). The implementation must either explain the extra platform effect with evidence and infer the LLVM-facing fields, or keep the rows approval-bound with a concrete reason.
   - Add unit tests for the global T20 solver, T12 exact-vs-upper-bound behavior, and vcpop.m m4 non-affine handling.
   - Regenerate `results/common/search_model_real_platform.json`, `results/common/real_platform_field_status.json`, `results/common/real_platform_inventory.json`, `results/common/experiment_quality.md`, the risk request hashes, and the Humanize2 prompt/tool-call/board/event/replay/cartridge capture.
   - Rerun `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`. The round is not complete until it exits 0, or the tracker clearly records remaining active blockers without a completion claim.

### HIGH 2. `real_platform_field_status.json` says no blocking rows even though 39 rows are gate-blocking

`scripts/search_model.py:2489-2495` builds the field-status summary with a local `blocking_statuses` set that omits `non_identifiable`. The generated sidecar therefore reports:

- `results/common/real_platform_field_status.json:32707-32708`: `"blocking_status_counts": {}` and `"blocking_total": 0`
- `results/common/real_platform_field_status.json:32716-32718`: `"status_counts": {"inferred": 111, "non_identifiable": 39}`

This contradicts the gate and quality-report semantics. Both `scripts/analyze.py:44-53` and `scripts/check_calibration_gate.py:56-65` include `non_identifiable` in their blocking status sets, and the quality report correctly reports the field-status summary as blocked (`results/common/experiment_quality.md:3650-3660`).

Risk: `real_platform_field_status.json` is hash-bound into the approval request (`real_platform_risk_acceptance_request.json:17-21`). A machine consumer or human reviewer reading the sidecar summary can incorrectly conclude that no approval-bound field-status blockers remain, undermining AC-16's confidence and approval boundary even though the gate itself still fails closed.

Required fix:

1. Make `scripts/search_model.py` use the same blocking status set as `scripts/analyze.py` and `scripts/check_calibration_gate.py`, or move the shared blocking-status definition into one importable helper to prevent future drift.
2. Add a regression test that constructs a report with at least one `non_identifiable` field row and asserts `summary.blocking_status_counts.non_identifiable == 1` and `summary.blocking_total == 1`.
3. Regenerate the real-platform search and derived artifacts. The new `real_platform_field_status.json` must report `blocking_total: 39` until approval or stronger evidence resolves the rows.
4. Refresh `results/common/real_platform_risk_acceptance_request.json` and all Humanize2 hash/capture artifacts because the field-status hash will change.

## Part 2: Goal Alignment Summary

ACs: 16/17 addressed | Forgotten items: 0 | Unjustified deferrals: 0

AC-1 through AC-15 and AC-17 remain previously addressed. AC-16 is still active and incomplete: the tracker already has T9 and T11 in `needs_changes`, no `Explicitly Deferred` item exists, and the open issue for the 39 non-identifiable rows remains valid. Round 8 did not modify the original plan and did not provide a valid plan evolution justification for treating AC-16 as complete.

The additional field-status summary bug is not currently tracked in `goal-tracker.md`. Because Claude's Round 8 summary did not include a `Goal Tracker Update Request`, I am recording the needed tracker change in this review result rather than moving tasks between tracker sections.

## Part 3: Goal Tracker Update Handling

Claude's Round 8 summary did not contain a `Goal Tracker Update Request`, so there was no requested task-completion move to approve.

Requested next tracker update:

- Add a Round 8 review entry to the Plan Evolution Log noting that AC-16 remains blocked and that `real_platform_field_status.json` undercounts approval-bound rows.
- Add an Open Issue for `real_platform_field_status.json` omitting `non_identifiable` from blocking counts.
- Keep T9 and T11 active as `needs_changes`.
- Do not modify the immutable section.

## Reviewer Verification Commands

- `git status --short --branch`: clean before reviewer edits; Round 8 commit `7a2315c7` only changed `round-8-summary.md`.
- `git show --stat --oneline --name-only HEAD`: confirmed the only Round 8 committed file is `.humanize/rlcr/2026-05-23_01-15-03/round-8-summary.md`.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no approval artifact found.
- Risk request versus inventory comparison: 39 request risk IDs, 39 inventory unresolved IDs, same order; request remains pending and not gate-consumed; current request hashes are inventory `4f25f066db09e0212200d48a181fd582e685701c16d18ca045dbc4738e4fb54b` and field status `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`.
- `python3 -m unittest tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval`: passed, 17 tests.
- `python3 -m pytest -q`: passed, 17 tests.
- `python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py`: passed.
- JSON parse for `results/common/agentic_flow/artifacts/tool_calls/*.json`: passed, 13 files.
- JSONL parse for `results/common/agentic_flow/events.jsonl`: passed, 46 events.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed on missing `Gate status: PASS`, missing machine-readable approval, and 39 unresolved `non_identifiable` risks.
- `git diff --check HEAD~1..HEAD`: passed.

REQUEST CHANGES
