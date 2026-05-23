# Round 10 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Round 10 makes real progress on the stronger-evidence path. The new T20 m4 no-reuse experiments, targeted `run_suite.py` selection filters, focused T12 scalar-filler experiments, regenerated real-platform artifacts, and Humanize2 capture are internally consistent with Claude's summary. The work is still not complete because AC-16 remains unmet: the real-platform gate is still `NOT_READY`, no machine-readable human approval artifact exists, and 38 LLVM-facing rows remain `non_identifiable`.

## Part 1: Implementation Review

### Accepted: focused evidence path was actually implemented

The Round 10 code/data commits are present after the last reviewed state:

- `f3bb455245cce28b1f61fd7447e1056e5c9903b2`: 108 generated T20 m4 no-reuse experiments plus global ProcResource solving support.
- `cd71b7ed3aa9d222306af23a51fe87efd76eddf9`: `run_suite.py` selection filters for `--template-id`, repeated `--id-regex`, and `--missing`.
- `c1032a2c01949ecb9d651473dec1aa88695bb484`: 54 focused T12 scalar-filler experiments and conservative T12/non-affine diagnostics.
- `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`: refreshed real gem5 repeats and regenerated search/profile/inventory/quality/request artifacts.
- `7a7da5d2`: Round 10 Humanize2 capture and summary.

Reviewer checks confirmed:

- `experiments/generated/suite_manifest.yaml` now has 3607 entries, including 108 `resource-noreuse` T20 entries and 54 `fscalar-add` T12 entries.
- `results/r01` and `results/r02` each contain 108 `resource-noreuse` traces and 54 `fscalar-add` traces.
- `results/common/search_model_real_platform.json` regenerates byte-for-byte from `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r10-review-search.json --format json`.
- `results/common/real_platform_field_status.json:33989-34005` reports 150 rows, 112 inferred rows, 38 `non_identifiable` rows, and `blocking_total: 38`.

### Accepted: pending request semantics remain safe

`results/common/real_platform_risk_acceptance_request.json:4-14` is Round 10, `pending`, `not_approved`, not submitted, not a gate input, not an approval artifact, and not gate-consumed. Its current hashes at `results/common/real_platform_risk_acceptance_request.json:17-21` match the live files. The 38 request risk IDs at `results/common/real_platform_risk_acceptance_request.json:30-68` match `results/common/real_platform_inventory.json` `field_status.unresolved` exactly.

`find results/common -maxdepth 1 -iname '*approval*' -print` produced no output.

### BLOCKER 1. AC-16 remains incomplete

The original plan requires real-platform profiling to stop on coverage, stability, confidence, documented assumptions, and explicit human approval before LLVM implementation (`docs/plan.md:735-749`, `docs/plan.md:1033`, `docs/plan.md:1058`). The current quality report is still fail-closed:

- `results/common/experiment_quality.md:3-13`: `Gate status: NOT_READY`, `Confidence: unresolved_llvm_field_status`, human approval absent, and 38 unresolved risks.
- `results/common/experiment_quality.md:3819-3824`: 112 inferred rows and 38 `non_identifiable` rows.
- `results/common/experiment_quality.md:3828-3865`: the remaining unresolved rows are still listed as approval-bound risks.
- `results/common/experiment_quality.md:3887-3890`: no approval artifact exists, and the real gate cannot pass without clean evidence or explicit per-risk acceptance tied to current hashes.

Reviewer reproduction:

```text
$ python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
FAIL: real_platform_profile gate did not pass using results/common/experiment_quality.md
- quality report must contain exact line `Gate status: PASS`
- missing machine-readable human approval file under results/common
- results/common/real_platform_inventory.json: unresolved real-platform LLVM field-status risks=38 status_counts={"non_identifiable": 38}
```

The 38 remaining rows are:

- 30 ProcResource rows with mirror/global assignment ambiguity.
- 5 T12 upper-bound-only Latency rows: `vcpop_m` m1/m2/m4, `vrgather_vv` m4, and `vslideup_vx` m4.
- 3 `vcpop_m` m4 issue-field rows: `ReleaseAtCycles`, `NumMicroOps`, and `SingleIssue`.

Required implementation plan for the next round:

1. Do not create `results/common/human_approval.json` unless the human owner supplies explicit approval for the current hashes and exact accepted risk IDs.
2. Resolve the 30 ProcResource rows by teaching the global ProcResource solver to detect pure global pipe-label mirror solutions. If every surviving global assignment differs only by swapping `pipe0` and `pipe1`, canonicalize the arbitrary label orientation with a deterministic symmetry breaker, record the symmetry-breaking assumption in search/profile/field-status artifacts, and mark the ProcResource rows exact only when relative resource identity is unique modulo that global swap. Add unit tests for pure mirror, non-mirror ambiguity, and real conflict cases.
3. Resolve the 5 T12 upper-bound-only Latency rows by adding matched dependent-vs-independent consumer control experiments under `T12_CONSUMER_RAW_GAP`. For each target row, generate and run K sweeps where the dependent consumer reads the producer result and a matched control consumer reads an initialized independent register with the same filler cadence and consumer kind. Update the T12 model to infer exact latency from the smallest K where dependent and control deltas converge, while preserving fail-closed behavior for noisy or non-monotonic controls.
4. Resolve the 3 `vcpop_m` m4 issue-field rows by adding a focused T10/T21 diagnostic sweep around the non-affine stream points. Generate contiguous counts around the first non-affine transition, vary scalar destination policy, mask/source register policy, and marker-alignment padding, then update the candidate simulator only if one explicit model explains all repeated observations. If no model explains the rows, AC-16 still requires current-hash human acceptance.
5. Regenerate `experiments/generated`, real gem5 repeats for only the new missing focused experiments, `search_model_real_platform.json`, profile sidecars, `real_platform_field_status.json`, `real_platform_inventory.json`, `experiment_quality.md`, and `real_platform_risk_acceptance_request.json`.
6. Refresh `results/common/agentic_flow/**` for the new evidence, run the focused unit tests plus `python3 -m pytest -q`, verify search artifact reproducibility with `cmp`, verify synthetic gate still passes, and require `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` to pass before any completion claim.

## Part 2: Goal Alignment Check

AC status:

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
| AC-9 | ADDRESSED, still contributes to AC-16 risk reduction |
| AC-10 | MET |
| AC-11 | MET |
| AC-12 | MET for Round 10 capture |
| AC-13 | MET for Round 10 replay/capture |
| AC-14 | MET |
| AC-15 | MET for synthetic-gated LLVM path |
| AC-16 | NOT MET |
| AC-17 | MET |

Forgotten items found: none. T9 and T11 remain active and correctly track the only completion blocker. No items are listed under Explicitly Deferred, and there are no unjustified deferrals. The Round 10 plan evolution is valid as progress, not completion.

Goal Alignment Summary:

```text
ACs: 17/17 addressed, 16/17 met | Forgotten items: 0 | Unjustified deferrals: 0
```

## Part 3: Goal Tracker Update Requests

Claude's tracker update request is approved as a progress update, not a completion update.

Changes applied to `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`:

- Updated Plan Version to 15 for Round 10 review.
- Added a Round 10 Plan Evolution Log entry for focused stronger-evidence work and the 39 to 38 risk reduction.
- Updated T6, T9, T10, T11, and T12 notes to the current Round 10 hashes and no-approval state.
- Added completed-and-verified evidence rows for commits `f3bb455245cce28b1f61fd7447e1056e5c9903b2`, `cd71b7ed3aa9d222306af23a51fe87efd76eddf9`, `c1032a2c01949ecb9d651473dec1aa88695bb484`, `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`, and `7a7da5d2`.
- Updated the open issue from 39 to 38 unresolved `non_identifiable` risks with the current hashes.
- Did not modify the immutable goal or acceptance criteria section.

## Reviewer Verification Commands

- `python3 -m unittest tests.test_run_suite_selection tests.test_gen_asm_t20_coverage tests.test_gen_asm_t12_focused tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval`: passed, 33 tests.
- `python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py`: passed.
- `python3 -m pytest -q`: passed, 33 tests.
- `git diff --check && git diff --cached --check`: passed after tracker update and review-result creation.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing PASS, missing approval, and 38 unresolved risks.
- `sha256sum` confirmed the current inventory, field-status, search, and quality hashes match the Round 10 request.
- Request risk IDs match inventory unresolved risk IDs exactly.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r10-review-search.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-r10-review-search.json results/common/search_model_real_platform.json`: passed.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no output.

REQUEST CHANGES
