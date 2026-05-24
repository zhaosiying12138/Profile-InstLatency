# Round 10 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Scope note: I read `docs/plan.md`, `.humanize/rlcr/2026-05-23_01-15-03/round-10-prompt.md`, and `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md` before reviewing. The live checkout is ahead of Claude's original Round 10 summary: the summary's 38-risk hashes are stale, and current HEAD reports 141 inferred rows plus 9 `non_identifiable` rows.

## Part 1: Implementation Review

### Accepted: Round 10 stronger-evidence work exists

The commits named in Claude's summary exist and match the claimed broad scope:

- `f3bb455245cce28b1f61fd7447e1056e5c9903b2`: T20 m4 no-reuse ProcResource evidence and global ProcResource solving support.
- `cd71b7ed3aa9d222306af23a51fe87efd76eddf9`: `run_suite.py` filters for `--template-id`, repeated `--id-regex`, and `--missing`.
- `c1032a2c01949ecb9d651473dec1aa88695bb484`: focused T12 scalar-filler evidence and conservative diagnostics.
- `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`: incremental real gem5 refresh plus regenerated search/profile/inventory/quality/request artifacts.
- Later current-head fixes also exist for real-search byte reproducibility, matched-control T12 exactness, formula-fit fail-closed coverage, and approval-status parser parity.

### BLOCKER 1. AC-16 remains incomplete

`docs/plan.md:740-749` and `docs/plan.md:1058` require real-platform profiling to stop on coverage, stability, confidence, documented assumptions, and explicit human approval before LLVM implementation. Current artifacts still fail that gate.

Evidence:

- `results/common/experiment_quality.md:4-13` reports `Gate status: NOT_READY`, unresolved LLVM field status, 9 unresolved risks, and absent explicit human approval.
- `results/common/experiment_quality.md:3863-3894` reports the failed confidence state, 141 inferred rows, and 9 `non_identifiable` rows.
- `results/common/experiment_quality.md:3919` says the real gate cannot pass without clean field-status evidence or per-risk acceptance plus approved human approval.
- `results/common/real_platform_risk_acceptance_request.json:25-39` records the current fail-closed reasons and exact 9 risk IDs.
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

### Accepted: Round 16 Humanize2 capture is finalized

AC-12 and AC-13 require replayable Humanize2 capture. The committed Round 15 capture replaces the approval-vocabulary parity placeholder with the committed boundary `f1687ac9`, and the Round 16 capture records approval-discovery scope commit `366be5b8`.

Evidence:

- `rg -n "pending_commit" results/common/agentic_flow` produces no output.
- `results/common/agentic_flow/events.jsonl:72` records `follow_up_commit: "f1687ac9"`.
- `results/common/agentic_flow/h2_primitives.yaml` records `vocabulary_parity: f1687ac9`.
- `results/common/agentic_flow/events.jsonl` records Round 16 approval-discovery scope completion for commit `366be5b8`.
- The execution, inference, experiment boards, worker output, normalized tool-call JSON, replay, status view, and draft cartridge all record the Round 16 boundary.

This fixes the replay-lineage content gap through the Round 16 boundary. It does not change the AC-16 real-platform gate outcome.

### Accepted: approval-discovery scope code fix is integrated

Commit `366be5b8` contains an approval-discovery scope fix: `scripts/analyze_quality.py` uses the shared `human_approval_file()` helper, `scripts/check_calibration_gate.py` delegates to the same helper, and `tests/test_check_calibration_gate_approval.py` has a nested-approval regression. Focused verification confirms nested `results/r01/**/human_approval.json` files are ignored by both analyzer discovery and gate lookup.

That fix is represented in the finalized Humanize2 workflow record: `h2_primitives.yaml`, `events.jsonl`, the boards, manifest notes, replay, status view, draft cartridge, and new prompt/contract/output/verification/tool-call/decision artifacts mention commit `366be5b8`. `boards/inference_state.yaml` keeps Round 15 approval-status fields under Round 15 and Round 16 approval-file-scope fields under Round 16.

Reviewer reproduction against current HEAD with a temporary nested `results/r01/some_instr/human_approval.json`:

```text
analyze_discover_approval= {'status': 'absent', 'approved': False, 'artifact_path': None, 'artifacts': []}
gate_approval_file= None
```

The live gate result is unchanged because there is still no approval artifact and 9 unresolved field-status risks remain.

## Required Implementation Plan

1. Continue the stronger-evidence path for AC-16 because no human approval artifact exists. Do not create `results/common/human_approval.json` unless the human owner supplies explicit approval tied to the current hashes and exact accepted risk IDs.
2. For the 5 remaining Latency rows, extend the matched dependent/control T12 path so observations produce a discriminating positive-stall equation rather than only an upper bound. Keep rows fail-closed if repeated evidence does not agree.
3. For the 4 `vcpop_m` `m4` issue/resource rows, implement and test one explicit model that explains all repeated T10/T21/R11 diagnostics. If any repeated diagnostic falsifies the model, keep those rows `non_identifiable` and preserve the evidence.
4. Add focused regression coverage in `tests/test_gen_asm_t12_focused.py`, `tests/test_gen_asm_vcpop_r11.py`, and `tests/test_search_model_candidate_sim.py` for every newly claimed field plus at least one falsified/non-identifiable path.
5. Regenerate affected generated experiments, real traces if new experiments are added, `results/common/search_model_real_platform.json`, `results/common/search_model_real_platform_summary.md`, per-instruction real-platform profile sidecars, `results/common/real_platform_field_status.json`, `results/common/real_platform_inventory.json`, `results/common/experiment_quality.md`, and `results/common/real_platform_risk_acceptance_request.json`.
6. Refresh `results/common/agentic_flow/**` again for any new evidence boundary with worker write scopes excluding `.humanize/rlcr/**`.
7. Verify `python3 -m pytest -q`, py_compile, real-search byte reproducibility, synthetic gate pass, and real gate status. Do not claim completion until `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` passes.

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
| AC-9 | MET at current HEAD |
| AC-10 | MET |
| AC-11 | MET |
| AC-12 | MET |
| AC-13 | MET |
| AC-14 | MET |
| AC-15 | MET for the synthetic-gated LLVM path |
| AC-16 | NOT MET: real-platform gate fails closed |
| AC-17 | MET |

Forgotten items found: none. There are no explicitly deferred tasks. T6/T12 are completed again after the Round 16 capture finalization; T9/T11 correctly remain `needs_changes` for AC-16.

Goal Alignment Summary:

```text
ACs: 17/17 addressed, 16/17 met, 1/17 not met | Forgotten items: 0 | Unjustified deferrals: 0
```

## Part 3: Goal Tracker Update Requests

Claude's original Round 10 tracker request was justified historically, and the current tracker already contains the Round 10 evidence rows plus later superseding current-head updates. Applying the request literally now would regress the tracker from the current 9-risk state back to stale 38-risk hashes, so I did not apply the stale request as written.

Mutable tracker state verified:

- Plan Version is now 34 for the Round 16 approval-discovery scope capture finalization.
- The Plan Evolution Log already records the unresolved `pending_commit` placeholders and the follow-up fix.
- T6 and T12 are completed again because approval-discovery commit `366be5b8` has finalized Humanize2 capture.
- The now-resolved Round 15 placeholder issue is not present in Open Issues.
- T9/T11 remain correctly preserved as `needs_changes` for the 9 unresolved real-platform risks and absent approval artifact.
- No new open issue remains for approval-discovery capture finalization.
- I did not modify the immutable Ultimate Goal or Acceptance Criteria.

## Reviewer Verification Commands

- `python3 -m pytest -q`: passed, 63 tests.
- `python3 -m py_compile scripts/approval_status.py scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/analyze_core.py scripts/analyze_quality.py scripts/run_experiment.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing PASS, missing approval, and 9 unresolved risks.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r10-review-search.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-r10-review-search.json results/common/search_model_real_platform.json`: passed.
- SHA for both regenerated and checked-in real search output: `3d72fd2e87b517e3e7ba3699eb214b8f35874055f3ed51c519aa4671d5f002bd`.
- Current hashes: inventory `197787ab2389df7a059aa9221a70dc5c03c4a18f7dade0c605aca939faa671fd`, field-status `079cb94d27e98bdcf9df0ae0595a6e12b101e4c8c5a3d46f7d627dd4c81c1432`, quality `d3c2e41f9bcd1a3b92ed2e148be5929d82a8ae111486c7471755030f7af1a31a`.
- Request risk IDs match inventory unresolved risk IDs exactly; request hashes match current files.
- YAML/JSON/JSONL parse checks passed for the reviewed Humanize2 artifacts, with 77 events.
- `rg -n "pending_commit" results/common/agentic_flow`: no output.
- Registered Humanize2 artifact path check: passed.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no output.
- `python3 -m unittest tests.test_check_calibration_gate_approval`: passed, 11 tests.
- Focused approval-discovery regression coverage confirms nested `results/r01/**/human_approval.json` files are ignored by both analyzer discovery and gate lookup.
- `git diff --check`: passed after writing this review update.

REQUEST CHANGES
