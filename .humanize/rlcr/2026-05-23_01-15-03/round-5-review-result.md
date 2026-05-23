# Round 5 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Round 5 fixes the two candidate-simulator bugs from the Round 4 review. The peer-side T20 mirroring is implemented, `vredsum_vs` now has peer-side T20 groups, the T12 K0/K1 short-sweep overclaim is covered by a regression test, and the real-platform search artifact regenerates byte-for-byte. The work is still not complete against `docs/plan.md`: Round 5 code-worker Humanize2 capture artifacts are missing, the remaining approval gate is too weak for the 39 `non_identifiable` rows, and AC-16 still lacks explicit machine-readable human approval.

## Part 1: Implementation Review

### Accepted: T20 peer-side constraints and T12 short-sweep guard

The `scripts/search_model.py` change mirrors T20 observations into existing peer rows (`scripts/search_model.py:774-783`, `scripts/search_model.py:2208-2219`) and keeps T20 checks grouped by the mirrored `(instruction_id, lmul, pair_instruction_id, register_policy)` key (`scripts/search_model.py:1119-1130`). The focused regression demonstrates that peer-only rows are constrained by mirrored observations (`tests/test_search_model_candidate_sim.py:174-217`).

The T12 exactness guard now requires a trailing minimum-residual/no-stall plateau before returning `exact` (`scripts/search_model.py:1265-1274`, `scripts/search_model.py:1401-1423`). The K0/K1 overclaim regression is present (`tests/test_search_model_candidate_sim.py:225-232`).

Artifact checks support Claude's claims:
- `vredsum_vs` no longer has empty T20 evidence; `m1`, `m2`, and `m4` have T20 groups in `results/common/search_model_real_platform.json`.
- `results/common/search_model_real_platform_summary.md:126-140` shows `vredsum_vs` fields are constrained with evidence counts 166/198.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r5-review-search.json --format json && cmp ...` reproduced the checked-in JSON.

### HIGH 1. Round 5 code-worker Humanize2 capture is incomplete

The original plan requires every coordinator/worker prompt and state-changing or verification tool call to be captured under `results/common/agentic_flow/` (`docs/plan.md:889-909`) and repeats that requirement in the per-round checklist (`docs/plan.md:1004-1011`). Claude's own summary says Round 5 had a candidate-simulator worker named Anscombe and a capture worker named Kepler (`.humanize/rlcr/2026-05-23_01-15-03/round-5-summary.md:4-12`).

The refreshed capture tree only registers the Round 5 capture worker. `h2_primitives.yaml` has one Round 5 prompt template, `round-5-capture-refresh` (`results/common/agentic_flow/h2_primitives.yaml:29-38`), and only `round-5-capture-*` contract/output/verification/tool-call artifacts (`results/common/agentic_flow/h2_primitives.yaml:188-203`). The code worker is represented only as `owner: other_worker` with `status: observed_pending_review` (`results/common/agentic_flow/h2_primitives.yaml:248-258`), and the boards still list the code fixes as pending review (`results/common/agentic_flow/boards/execution_state.yaml:29-31`, `results/common/agentic_flow/boards/execution_state.yaml:73-77`).

Risk: AC-12/AC-13 are still partial. An empty-context Humanize2 replay cannot reconstruct the Round 5 code-worker prompt, allowed write scope, success criteria, state-changing commands, artifact regeneration commands, or verification evidence without relying on the chat transcript or the commit message.

Required fix:
1. Add Round 5 candidate-simulator/code-worker artifacts under `results/common/agentic_flow/artifacts/`: prompt, worker contract, worker output, verification report, and normalized tool-call JSON for code edits/regeneration/tests/gates/hash checks.
2. Register those artifacts in `results/common/agentic_flow/h2_primitives.yaml` as `h2-template` and `h2-artifact` entries.
3. Append events for code-worker dispatch, completion, artifact regeneration, verification, and review outcome.
4. Update boards, replay, status panel, and cartridge so `773f27d6` is no longer merely `pending_review` and the approval boundary remains explicit.
5. Verify YAML/JSON, registered path existence, stale `pending_review` wording for the reviewed code fix, and `git diff --check`.

### HIGH 2. AC-16 approval validation is too weak for the 39 non-identifiable rows

The current quality report records 39 `non_identifiable` rows but then says there are no unresolved field-status risks (`results/common/experiment_quality.md:3655-3659`). The inventory does the same: it records `non_identifiable: 39` and `unresolved_total: 0` (`results/common/real_platform_inventory.json:1140-1160`) while setting `field_status_unresolved_risks_accepted: true` with no accepted risk IDs (`results/common/real_platform_inventory.json:102996-102998`).

This happens because `non_identifiable` is not a blocking field status (`scripts/analyze.py:44-52`), unresolved rows are computed only from blocking statuses (`scripts/analyze.py:1456-1466`), and empty unresolved lists are treated as accepted (`scripts/analyze.py:1538-1542`). The checker then requires a `real_platform_field_status_sha256` only when `field_status.unresolved_total` is nonzero (`scripts/check_calibration_gate.py:659-670`), while a generic tie such as `trace_count` can satisfy the broader approval tie check (`scripts/check_calibration_gate.py:625-642`).

Risk: a future approval artifact could pass validation without explicitly binding acceptance to the current `real_platform_field_status.json` hash or to the 39 non-identifiable risk rows. That does not satisfy the Round 4/Round 5 stated approval boundary or AC-16's "confidence, documented assumptions, and explicit human approval" requirement.

Required fix:
1. Treat `non_identifiable` rows as approval-bound risks unless stronger evidence resolves them.
2. Require any approval for real-platform completion to include both `inventory_sha256` and `real_platform_field_status_sha256` matching the current artifacts.
3. Require explicit accepted risk IDs or an explicit all-risks acceptance covering the 39 non-identifiable rows.
4. Add checker tests proving that approval files with only trace counts, stale hashes, or missing accepted-risk scope fail.
5. Regenerate `real_platform_inventory.json` and `experiment_quality.md` so the quality report no longer says "No unresolved field-status risks" while 39 rows still need acceptance.

### BLOCKER 3. AC-16 remains fail-closed and incomplete

This is expected behavior, but it prevents completion. `results/common/experiment_quality.md:3-12` reports `Gate status: NOT_READY`, `Confidence: awaiting_human_approval`, and absent approval. The real-platform gate fails on exactly:

```text
FAIL: real_platform_profile gate did not pass using results/common/experiment_quality.md
- quality report must contain exact line `Gate status: PASS`
- missing machine-readable human approval file under results/common
```

No `results/common/*approval*` artifact exists. Do not output `COMPLETE` until the approval boundary is hardened, the required human approval artifact exists and is hash/risk-bound, and `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` passes.

## Part 2: Goal Alignment Summary

ACs: 14/17 met | Forgotten items: 2 | Unjustified deferrals: 0

Met or addressed: AC-1 through AC-11, AC-14, AC-15, AC-17, and AC-9 for the candidate-simulator scope.

Partial: AC-12 and AC-13. Round 5 removed the stale Round 1/T01-only replay claims, but the Round 5 code-worker prompt/tool-call capture is still missing.

Not met: AC-16. The real-platform gate lacks explicit machine-readable human approval and the 39 non-identifiable rows still require stronger evidence/modeling or explicit risk acceptance tied to current hashes.

No explicit deferrals are listed in the tracker. The remaining approval item is not a justified completion deferral; it is an active blocker.

## Part 3: Goal Tracker Update Handling

I updated `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`.

Approved:
- Marked the Round 4 T20 peer-side and T12 short-sweep issues as resolved by `773f27d6`.
- Marked T10 raw-observation parameter search as completed for AC-9/AC-10.
- Updated current real-platform hashes to:
  - `real_platform_inventory.json`: `d29e632b98c0a5734d541939c561872eeed691fd3c00b7ea83cf8aea666a536d`
  - `real_platform_field_status.json`: `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`
- Kept T9/T11 active because AC-16 still fails closed.

Rejected or modified:
- Did not mark T6/T12 completed. The stale Round 1 replay issue is fixed, but Round 5 code-worker capture artifacts are missing.
- Did not reduce open issues to only a generic approval item. Approval validation itself needs hardening before AC-16 can be accepted.

## Required Next Implementation Plan

1. Complete the missing Round 5 code-worker Humanize2 capture package and register it in `h2_primitives.yaml`.
2. Harden `scripts/analyze.py` and `scripts/check_calibration_gate.py` so the 39 `non_identifiable` rows are approval-bound risks and approval must include current inventory and field-status hashes plus accepted risk scope.
3. Add focused approval-gate regressions for missing hashes, stale hashes, trace-count-only approval, and valid all-risks acceptance.
4. Regenerate real-platform inventory and quality artifacts.
5. Re-run: unit tests, full pytest, py_compile, real search regeneration/cmp, synthetic gate, expected real gate failure if no human approval exists, JSON/YAML/JSONL checks, and `git diff --check`.

## Reviewer Verification Commands

- `python3 -m unittest tests.test_search_model_candidate_sim`: passed, 10 tests.
- `python3 -m pytest -q`: passed, 10 tests in 56.63s.
- `python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py`: passed.
- JSON/JSONL validation for real-platform artifacts and `events.jsonl`: passed.
- YAML validation for agentic-flow boards and `h2_primitives.yaml`: passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r5-review-search.json --format json && cmp ...`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed as expected on missing PASS and missing approval.
- `find results/r01 results/r02 -name trace.json | wc -l`: `7190`.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: empty.
- `sha256sum` matched Claude's reported Round 5 hashes.

REQUEST CHANGES
