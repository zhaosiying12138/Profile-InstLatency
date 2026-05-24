# Round 10 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Scope note: I read `docs/plan.md`, `.humanize/rlcr/2026-05-23_01-15-03/round-10-prompt.md`, and `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md` before reviewing. The submitted Round 10 summary is accurate for its original boundary through `7a7da5d2`, but the live checkout has advanced beyond that boundary. Do not use the summary's 38-risk hashes as current state. Current HEAD reports 141 inferred rows, 9 `non_identifiable` rows, request round 14, and search hash `3d72fd2e87b517e3e7ba3699eb214b8f35874055f3ed51c519aa4671d5f002bd`.

## Part 1: Implementation Review

### Accepted: Round 10 and follow-up evidence are real progress

The commits named in Claude's Round 10 summary exist and match the claimed scope:

- `f3bb455245cce28b1f61fd7447e1056e5c9903b2`: T20 m4 no-reuse ProcResource evidence and global ProcResource solving support.
- `cd71b7ed3aa9d222306af23a51fe87efd76eddf9`: `run_suite.py` filters for `--template-id`, repeated `--id-regex`, and `--missing`.
- `c1032a2c01949ecb9d651473dec1aa88695bb484`: focused T12 scalar-filler evidence and conservative diagnostics.
- `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`: incremental real gem5 refresh plus regenerated search/profile/inventory/quality/request artifacts.
- `7a7da5d2`: Round 10 Humanize2 capture and summary.

The later current-head fixes are also present and verified: search byte-reproducibility is fixed, matched-control T12 exactness is fixed, worker control-plane write scope no longer grants `.humanize/rlcr/**`, formula fits now report `partial_fit_blocked` when required `m1`/`m2`/`m4` coverage is incomplete, the contradictory pending/approved approval parser hole is fixed, analyzer discovery and gate validation now share top-level approval vocabulary, and Round 15 Humanize2 capture records the approval-status hardening boundary. `results/common/search_model_real_platform_summary.md:195-209` shows the previously risky `vcpop_m`, `vrgather_vv`, and `vslideup_vx` formula rows fail closed instead of claiming complete exact formulas.

### BLOCKER 1. AC-16 is still incomplete

`docs/plan.md:740-749` and `docs/plan.md:1058` require real-platform profiling to stop on coverage, stability, confidence, documented assumptions, and explicit human approval before LLVM implementation. Current artifacts still do not satisfy that gate.

Evidence:

- `results/common/experiment_quality.md:3-13` reports `Gate status: NOT_READY`, `Confidence: unresolved_llvm_field_status`, human approval absent, and 9 unresolved risks.
- `results/common/experiment_quality.md:3863-3866` lists failed checks `required_llvm_field_status_clean_or_accepted` and `explicit_human_approval`.
- `results/common/experiment_quality.md:3877-3894` reports 141 inferred rows and 9 `non_identifiable` rows.
- `results/common/experiment_quality.md:3916-3919` confirms no approval artifact exists and the real gate cannot pass without clean evidence or accepted risks plus approved human approval.
- `results/common/real_platform_risk_acceptance_request.json:6-14` is explicitly pending/not approved/not submitted/not a gate input/not an approval artifact/not gate-consumed.
- `results/common/real_platform_risk_acceptance_request.json:17-39` binds the current request hashes and exact 9 risk IDs.
- `find results/common -maxdepth 1 -iname '*approval*' -print` produced no output.

Reviewer reproduction:

```text
$ python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
FAIL: real_platform_profile gate did not pass using results/common/experiment_quality.md
- quality report must contain exact line `Gate status: PASS`
- missing machine-readable human approval file under results/common
- results/common/real_platform_inventory.json: unresolved real-platform LLVM field-status risks=9 status_counts={"non_identifiable": 9}
```

Remaining rows:

- `vcpop_m` Latency for `m1`, `m2`, and `m4`.
- `vcpop_m` `m4` `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue`.
- `vrgather_vv` `m4` Latency.
- `vslideup_vx` `m4` Latency.

Required implementation plan:

1. Continue the stronger-evidence path because no human approval artifact exists in the repository. Do not create `results/common/human_approval.json` unless the human owner supplies an explicit approval decision tied to the current hashes and exact accepted risk IDs.
2. For the 5 remaining Latency rows, extend the existing matched dependent/control T12 path in `scripts/gen_asm.py` and `scripts/search_model_impl.py` so the real observations produce a discriminating positive-stall equation rather than only an upper bound. Keep the current fail-closed behavior for any row that still lacks stable agreement.
3. For the 4 `vcpop_m` `m4` issue/resource rows, implement and test one explicit model that explains all repeated T10/T21/R11 diagnostics. If the model is falsified by any repeated diagnostic, keep those rows `non_identifiable` and preserve the evidence instead of inventing LLVM-facing fields.
4. Add focused regression coverage in `tests/test_gen_asm_t12_focused.py` and `tests/test_search_model_candidate_sim.py` for every newly claimed field and for at least one falsified/non-identifiable path.
5. Regenerate `results/common/search_model_real_platform.json`, `results/common/search_model_real_platform_summary.md`, per-instruction profile sidecars if affected, `results/common/real_platform_field_status.json`, `results/common/real_platform_inventory.json`, `results/common/experiment_quality.md`, and `results/common/real_platform_risk_acceptance_request.json`.
6. Refresh `results/common/agentic_flow/**` for the new evidence boundary, keeping worker write scopes out of `.humanize/rlcr/**`.
7. Verify `python3 -m pytest -q`, py_compile, real-search byte reproducibility, synthetic gate pass, and real gate status. Do not claim completion until `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` passes.

### Accepted: future human approval validation is hardened

The approval-status issue found during re-review is now fixed. `scripts/approval_status.py` defines the shared top-level approval decision helper used by both `scripts/check_calibration_gate.py` and `scripts/analyze_quality.py`. Every present top-level approval/status field must be approved/granted/pass. Nested `risk_acceptance.status` no longer satisfies artifact-level approval.

`scripts/analyze.py`/`scripts/analyze_quality.py` now reject the contradictory `status: pending` plus nested `risk_acceptance.status: approved` case, while recursive extraction is still used for accepted risk IDs and risk-acceptance scope. The analyzer and gate now share the top-level vocabulary `approved`, `human_approved`, `human_approval`, `status`, `human_approval_status`, and `approval_status`.

Regression coverage in `tests/test_check_calibration_gate_approval.py` verifies:

- top-level `status: pending` plus nested `risk_acceptance.status: approved` fails approval validation and remains unapproved in `analyze.discover_approval()`.
- top-level approved plus nested accepted-risk scope remains valid.
- top-level `human_approved: true` is accepted consistently by analyzer discovery and gate validation.

This does not make the real-platform gate pass, because no approval artifact exists and the 9 non-identifiable rows remain unresolved.

### Accepted: analyzer and gate approval vocabulary now match

The approval-reporting path and the gate now share `scripts/approval_status.py`. The canonical top-level vocabulary includes `human_approved` on both paths. Accepted-risk extraction remains recursive, but artifact approval status is top-level only.

Regression coverage in `tests/test_check_calibration_gate_approval.py` creates `human_approval.json` with top-level `human_approved: true`, current hashes, and accepted risks, then asserts analyzer discovery and gate validation agree and pass the unresolved field-status risk scope.

### Accepted: current-head approval parser hardening is captured in Humanize2 state

Round 15 capture now records commit `9a85412b` and the follow-up vocabulary repair under `results/common/agentic_flow/**`.

Captured surfaces:

- `results/common/agentic_flow/artifacts/prompts/round-15-approval-status-hardening-worker.md`
- `results/common/agentic_flow/artifacts/worker_contracts/worker-r15-approval-status-hardening.md`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-r15-approval-status-hardening.md`
- `results/common/agentic_flow/artifacts/verification/worker-r15-approval-status-hardening.md`
- `results/common/agentic_flow/artifacts/tool_calls/worker-r15-approval-status-hardening-normalized.json`
- `results/common/agentic_flow/artifacts/decisions/round-15-approval-status-hardening.md`
- `h2_primitives.yaml`, `events.jsonl`, replay, boards, status view, draft cartridge, and manifest notes.

The capture preserves request semantics: no approval artifact exists, the current request remains pending/not approved/not gate-consumed, and the real-platform gate still fails closed on the 9 unresolved risks.

## Part 2: Goal Alignment Check

Current AC status:

| AC | Status |
| --- | --- |
| AC-1 | MET |
| AC-2 | MET |
| AC-3 | MET |
| AC-4 | MET |
| AC-5 | MET |
| AC-6 | MET |
| AC-7 | MET |
| AC-8 | MET |
| AC-9 | MET at current HEAD after the T12 exactness and formula-fit coverage fixes |
| AC-10 | MET |
| AC-11 | MET |
| AC-12 | MET |
| AC-13 | MET |
| AC-14 | MET |
| AC-15 | MET for the synthetic-gated LLVM path |
| AC-16 | NOT MET |
| AC-17 | MET |

Forgotten items found: none. `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md` has no explicitly deferred tasks and now keeps the current 9-risk AC-16 blocker open. T6 and T12 are completed again for Round 15 capture; T9 and T11 remain `needs_changes`, which is correct.

Goal Alignment Summary:

```text
ACs: 17/17 addressed, 16/17 met | Forgotten items: 0 | Unjustified deferrals: 0
```

## Part 3: Goal Tracker Update Requests

Claude's Round 10 tracker request was justified as a progress update, not a completion update, but it is now superseded by later current-head tracker state. I applied an additional mutable tracker update for the approval-status validation blocker, recorded its fix, reopened AC-12/AC-13 for the missing Humanize2 capture, and then closed that capture/vocabulary follow-up with Round 15 evidence.

Current tracker state already records:

- Plan Version 29 at `goal-tracker.md:52`.
- Round 10 progress for `f3bb4552`, `cd71b7ed`, `c1032a2c`, `73b99c2e`, and `7a7da5d2` at `goal-tracker.md:73`.
- The formula-fit coverage repair at `goal-tracker.md:81`.
- The approval-status gate hardening issue, fix, capture gap, approval-report vocabulary mismatch, and Round 15 fix at `goal-tracker.md:82-86`.
- T6/T12 as `completed` after Round 15 capture refresh, and T9/T11 as `needs_changes` until AC-16 passes.
- The current open issue for 9 non-identifiable real-platform LLVM-facing rows.

The immutable goal and acceptance criteria were not modified.

## Reviewer Verification Commands

- Red check for `test_human_approved_top_level_status_has_analyzer_gate_parity`: failed before the shared helper because analyzer discovery accepted `human_approved` while gate validation rejected it.
- `python3 -m unittest tests.test_check_calibration_gate_approval`: passed, 10 tests.
- `python3 -m pytest -q`: passed, 62 tests.
- `python3 -m py_compile scripts/approval_status.py scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/analyze_core.py scripts/analyze_quality.py scripts/run_experiment.py`: passed.
- `python3 scripts/analyze.py --all --dry-run`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing PASS, missing approval, and 9 unresolved risks.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-round15-review-search.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-round15-review-search.json results/common/search_model_real_platform.json`: passed.
- SHA for both regenerated and checked-in real search output: `3d72fd2e87b517e3e7ba3699eb214b8f35874055f3ed51c519aa4671d5f002bd`.
- YAML/JSON/JSONL parse for `results/common/agentic_flow/h2_primitives.yaml`, boards, tool-call JSON, request JSON, and `events.jsonl`: passed, 74 events; registered path checks passed.
- Humanize2 capture freshness check: `results/common/agentic_flow/**` now mentions `9a85412b`, `approval-status`, `human_approved`, and `Round15ApprovalStatusHardening`.
- Formula-fit probe reports `partial_fit_blocked` with blocked `m4` for `vcpop_m` `ReleaseAtCycles`, `vrgather_vv` `Latency`, and `vslideup_vx` `Latency`.
- Request risk IDs match inventory unresolved risk IDs exactly.
- Approval-status regression now rejects top-level `status: pending` when a nested risk-acceptance object has `status: approved`, and still accepts top-level approved plus nested accepted-risk scope.
- Approval-vocabulary parity regression: top-level `human_approved: true` is accepted consistently by analyzer approval discovery and gate validation.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no output.
- `git diff --check` and `git diff --cached --check`: passed after this review-result/tracker update.

REQUEST CHANGES
