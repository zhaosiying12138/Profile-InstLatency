# Round 6 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Round 6 correctly resolves the Round 5 approval-gate bug: `non_identifiable` rows are now unresolved approval-bound risks, approval must bind the current inventory and field-status hashes, focused tests cover stale/missing hash and risk-scope failures, and the real-platform gate fails closed on 39 unresolved risks plus absent approval. The Round 5 code-worker capture package is also present and registered.

The work is still not complete against `docs/plan.md`. Round 6 introduced a new approval-gate worker/commit, but the Humanize2 replay tree captures only the Round 5 code worker and still records Round 5 hashes as current. AC-16 also remains explicitly incomplete because no machine-readable human approval artifact exists and 39 real-platform LLVM-facing rows remain unresolved.

## Part 1: Implementation Review

### Accepted: approval-bound real-platform risk hardening

`scripts/analyze.py:44-53` now treats `non_identifiable` as a blocking field status. `scripts/check_calibration_gate.py:56-74` mirrors that status set and defines accepted all-risk sentinels. `scripts/check_calibration_gate.py:648-729` extracts accepted risk IDs and requires unresolved risk coverage; `scripts/check_calibration_gate.py:807-826` requires current `inventory_sha256` and `real_platform_field_status_sha256`; `scripts/check_calibration_gate.py:840-884` fails the real gate when unresolved field-status risks are not covered by a valid approval.

The focused regression tests cover the required failure modes: trace-count-only approval fails hash binding, stale inventory hash fails, stale field-status hash fails, missing field-status hash fails, stale inventory-side acceptance without approval risk scope fails, and explicit all-risks acceptance succeeds (`tests/test_check_calibration_gate_approval.py:88-217`).

The regenerated quality report is no longer falsely clean: it reports `Gate status: NOT_READY`, `Confidence: unresolved_llvm_field_status`, `Human approval status: absent`, and 39 unresolved `non_identifiable` risks (`results/common/experiment_quality.md:3-13`, `results/common/experiment_quality.md:3648-3662`, `results/common/experiment_quality.md:3726-3729`).

### Accepted: Round 5 code-worker capture backfill

The Round 5 code-worker prompt, contract, output, verification, and normalized tool-call artifacts exist and are registered in `h2_primitives.yaml` (`results/common/agentic_flow/h2_primitives.yaml:39-41`, `results/common/agentic_flow/h2_primitives.yaml:191-206`). The stale `pending_review` / `observed_pending_review` wording is absent from `results/common/agentic_flow/`, and the Round 5 code worker is now represented as a reviewed `h2-agent` flow node (`results/common/agentic_flow/h2_primitives.yaml:272-283`).

### HIGH 1. Round 6's own approval-gate worker is not captured, and replay state is stale

The original plan requires every coordinator/worker prompt to be saved and registered (`docs/plan.md:889-899`), every state-changing or verification tool call to be saved as normalized JSON (`docs/plan.md:901-915`), events for dispatch/completion/verification/decisions (`docs/plan.md:918-943`), and per-round updates to boards, prompts, tool calls, events, cartridge, and summary (`docs/plan.md:1004-1011`).

Claude's Round 6 summary says Worker Gibbs completed approval-gate hardening in commit `ea7c0aca`, changing `scripts/analyze.py`, `scripts/check_calibration_gate.py`, `tests/test_check_calibration_gate_approval.py`, `results/common/real_platform_inventory.json`, and `results/common/experiment_quality.md` (`.humanize/rlcr/2026-05-23_01-15-03/round-6-summary.md:9-23`). The agentic-flow tree does not capture that worker. `h2_primitives.yaml` registers only the Round 5 code-worker template and artifacts, with no Round 6/Gibbs/`ea7c0aca` prompt, worker contract, output, verification, tool-call artifact, event type, or flow node (`results/common/agentic_flow/h2_primitives.yaml:29-41`, `results/common/agentic_flow/h2_primitives.yaml:191-249`, `results/common/agentic_flow/h2_primitives.yaml:272-288`).

The replay and boards are also stale after the Round 6 artifact regeneration. `replay.md` calls the current evidence snapshot "Round 5 boundary hashes" and lists the old inventory hash `d29e632b...` and old quality hash `6062c76f...` (`results/common/agentic_flow/replay.md:82-100`). `execution_state.yaml` likewise records those old hashes as current (`results/common/agentic_flow/boards/execution_state.yaml:48-52`), while the actual current hashes are inventory `4f25f066db09e0212200d48a181fd582e685701c16d18ca045dbc4738e4fb54b` and quality `b6b6b1dde2095c59b43b702cfc53ec075b45982a2ff6ea0ee9fba12ab30bb5f6` (`.humanize/rlcr/2026-05-23_01-15-03/round-6-summary.md:49-53`). `h2_primitives.yaml` also says approval must bind to the stale inventory hash `d29e632b...` (`results/common/agentic_flow/h2_primitives.yaml:292-299`).

Risk: AC-12 and AC-13 are still partial. An empty-context replay can reconstruct the Round 5 candidate-simulator worker, but it cannot reconstruct the Round 6 approval-gate hardening work, its state-changing commands, or the current approval-bound hash snapshot. Worse, following the current replay approval boundary would bind future approval to the stale Round 5 inventory hash instead of the current Round 6 inventory hash.

Required fix:

1. Add Round 6 Worker Gibbs capture artifacts under `results/common/agentic_flow/artifacts/`: prompt, worker contract, worker output, verification report, and normalized tool-call JSON for the approval-gate code edits, test edits, artifact regeneration, gate checks, hash checks, and no-approval search.
2. Register the new prompt and artifacts in `results/common/agentic_flow/h2_primitives.yaml` as `h2-template` and `h2-artifact` entries.
3. Add a Round 6 approval-gate `h2-agent` flow node for Worker Gibbs, including commit `ea7c0aca`, owned write scope, verification artifacts, and fail-closed approval boundary.
4. Append `events.jsonl` records for Round 6 approval-gate worker dispatch, completion, artifact regeneration, verification, real-gate fail-closed result, and review outcome capture.
5. Update `boards/*.yaml`, `replay.md`, `h2_manifest_notes.md`, `views/status_panel.html`, and `cartridges/rvv-profile-workflow.draft.html` so the current Round 6 hashes are:
   - `real_platform_inventory.json`: `4f25f066db09e0212200d48a181fd582e685701c16d18ca045dbc4738e4fb54b`
   - `real_platform_field_status.json`: `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`
   - `search_model_real_platform.json`: `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73`
   - `experiment_quality.md`: `b6b6b1dde2095c59b43b702cfc53ec075b45982a2ff6ea0ee9fba12ab30bb5f6`
6. Remove stale text saying approval validation still needs hardening. Keep the remaining approval blocker as explicit human approval or stronger evidence for the 39 unresolved risks.
7. Verify YAML/JSON/JSONL parsing, registered path existence, `rg -n "Gibbs|ea7c0aca|4f25f066|b6b6b1dd" results/common/agentic_flow`, absence of stale Round 5 "current hash" records, full tests, gates, search regeneration/cmp, and `git diff --check`.

### BLOCKER 2. AC-16 remains incomplete without explicit approval or stronger evidence

This is not a code bug in Round 6, but it is a completion blocker under the original plan. `AC-16` requires real-platform profiling to stop only on coverage, stability, confidence, documented assumptions, and explicit human approval before LLVM implementation. Current evidence is still `NOT_READY`: no approval artifact exists, and 39 `non_identifiable` LLVM-facing rows remain unresolved (`results/common/experiment_quality.md:3-13`, `results/common/experiment_quality.md:3648-3662`, `results/common/experiment_quality.md:3726-3729`).

Reviewer verification reproduced the expected fail-closed gate:

```text
FAIL: real_platform_profile gate did not pass using results/common/experiment_quality.md
- quality report must contain exact line `Gate status: PASS`
- missing machine-readable human approval file under results/common
- results/common/real_platform_inventory.json: unresolved real-platform LLVM field-status risks=39 status_counts={"non_identifiable": 39}
```

Required completion plan:

1. After fixing the Round 6 capture gap, generate a machine-readable approval request artifact that lists the current inventory hash, field-status hash, all 39 risk IDs, and the exact gate command that will be rerun. This request artifact must not be named as an approval artifact and must not satisfy the gate.
2. Ask the human owner for explicit approval of those exact risks and hashes. Do not synthesize approval from prior summaries, commit messages, or inventory-side stale acceptance.
3. If approval is granted, create `results/common/human_approval.json` with `status: approved`, `approved_by`, current `inventory_sha256`, current `real_platform_field_status_sha256`, and either all 39 accepted risk IDs or `accepted_risk_ids: all`; rerun the real-platform gate and regenerate/report hashes.
4. If approval is not granted, implement additional discriminating experiments/modeling until `real_platform_field_status.json` has no unresolved blocking rows, regenerate inventory and quality artifacts, and rerun the real-platform gate.
5. Do not output `COMPLETE` until `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` exits 0 and the approval or stronger-evidence path is captured in Humanize2 replay.

## Part 2: Goal Alignment Summary

ACs: 14/17 addressed | Forgotten items: 1 | Unjustified deferrals: 0

Fully addressed or previously accepted: AC-1 through AC-11, AC-14, AC-15, and AC-17.

Partial: AC-12 and AC-13. Round 6 fixed the Round 5 code-worker capture gap, but forgot to capture the Round 6 approval-gate worker and left replay/boards with stale Round 5 hashes.

Not met: AC-16. The real-platform gate still lacks explicit machine-readable human approval and has 39 approval-bound unresolved field-status risks.

No explicit deferrals are recorded in the tracker. The remaining approval item is an active blocker, not a justified deferral.

## Part 3: Goal Tracker Update Handling

I updated `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`.

Approved:

- Marked the Round 5 code-worker capture issue as resolved by commit `7a76e62f`.
- Marked the approval-validation weakness as resolved by commit `ea7c0aca`.
- Added completed-and-verified entries for the Round 5 capture backfill and T11 approval-bound field-status hardening.
- Updated T9/T11 notes and the 39-risk open issue to the Round 6 hashes and hash/risk-bound approval requirements.

Rejected or modified:

- Did not mark T6/T12 or AC-12/AC-13 complete. Round 6's own approval-gate worker capture is missing, and the replay/board approval hashes are stale.
- Kept T9/T11 and AC-16 active until explicit machine-readable human approval exists or stronger evidence removes all 39 unresolved risks and the real-platform gate passes.
- Added a new open issue for the missing Round 6 approval-gate Humanize2 capture and stale replay hashes.

## Reviewer Verification Commands

- `python3 -m unittest tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval`: passed, 17 tests.
- `python3 -m pytest -q`: passed, 17 tests in 57.34s.
- `python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing PASS, missing approval, and 39 unresolved `non_identifiable` risks.
- YAML parse for `results/common/agentic_flow/h2_primitives.yaml` and all `boards/*.yaml`: passed.
- JSON parse for `results/common/agentic_flow/artifacts/tool_calls/*.json`: passed.
- JSONL parse for `results/common/agentic_flow/events.jsonl`: passed.
- Registered path existence check for `templates`, `boards`, and `artifacts`: passed.
- JSON validation passed for `results/common/real_platform_inventory.json`, `results/common/real_platform_field_status.json`, and `results/common/search_model_real_platform.json`.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r6-review-search.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-r6-review-search.json results/common/search_model_real_platform.json`: passed.
- `sha256sum` confirmed `search_model_real_platform.json` hash `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73`, inventory hash `4f25f066db09e0212200d48a181fd582e685701c16d18ca045dbc4738e4fb54b`, and quality hash `b6b6b1dde2095c59b43b702cfc53ec075b45982a2ff6ea0ee9fba12ab30bb5f6`.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: empty.
- `git diff --check`: passed.

REQUEST CHANGES
