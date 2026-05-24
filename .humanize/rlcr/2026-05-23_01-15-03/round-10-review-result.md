# Round 10 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Scope note: I read `docs/plan.md`, `.humanize/rlcr/2026-05-23_01-15-03/round-10-prompt.md`, and `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md` before reviewing. The strict Round 10 summary is accurate for commits through `7a7da5d2`: Round 10 added focused T20/T12 evidence, refreshed real-platform artifacts, reduced unresolved rows from 39 to 38, and kept the request pending rather than approved. Current `HEAD` is now past that boundary at `418a24ab`, after follow-up commits including `77d181af`, `6ff16b7c`, `88c9e6e5`, `8ec7a8a8`, `fbc490b4`, and `91201d20`; current artifacts report 141 inferred rows and 9 `non_identifiable` rows.

## Part 1: Implementation Review

### Accepted: Round 10 focused-evidence work was real progress

The commits named in Claude's summary exist and match the claimed scope:

- `f3bb455245cce28b1f61fd7447e1056e5c9903b2`: T20 m4 no-reuse ProcResource evidence and global ProcResource solving support.
- `cd71b7ed3aa9d222306af23a51fe87efd76eddf9`: `run_suite.py` filters for `--template-id`, repeated `--id-regex`, and `--missing`.
- `c1032a2c01949ecb9d651473dec1aa88695bb484`: focused T12 scalar-filler evidence and conservative diagnostics.
- `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`: incremental real gem5 refresh plus regenerated search/profile/inventory/quality/request artifacts.
- `7a7da5d2`: Round 10 Humanize2 capture and summary.

That boundary was progress, not completion, because AC-16 remained fail-closed.

### Accepted: current-head search reproducibility is fixed

The previous current-head review finding that search output was not byte-reproducible is now resolved by `8ec7a8a8`.

Reviewer reproduction:

```text
$ python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r10-review-current-search.json --format json
wrote /tmp/profile-inst-latency-r10-review-current-search.json

$ cmp /tmp/profile-inst-latency-r10-review-current-search.json results/common/search_model_real_platform.json
<no output; exit 0>

$ sha256sum /tmp/profile-inst-latency-r10-review-current-search.json results/common/search_model_real_platform.json
2f3b78ebfd2e499bcd2420a9052e361fa63320ba801c7a155638b83d1975d6b6  /tmp/profile-inst-latency-r10-review-current-search.json
2f3b78ebfd2e499bcd2420a9052e361fa63320ba801c7a155638b83d1975d6b6  results/common/search_model_real_platform.json
```

Focused tests also cover the wrapper split and `/tmp` output behavior.

### Accepted: current-head Humanize2 capture is now present

The current worktree includes a Round 11/current-head capture package under `results/common/agentic_flow/**` for `77d181af`, `6ff16b7c`, `88c9e6e5`, and `8ec7a8a8`. It includes prompt, contract, worker output, verification, normalized tool-call JSON, boards, events, replay, status view, draft cartridge, and manifest notes. YAML/JSON/JSONL parsing passed.

The capture correctly preserves request semantics: `results/common/real_platform_risk_acceptance_request.json` remains pending, not approved, not submitted, not a gate input, not an approval artifact, and not gate-consumed.

### Accepted: matched-control T12 exactness is fixed

The matched-control exactness bug found during review is now fixed by `91201d20`. `t12_matched_control_constraint()` derives exact latency from all positive-stall equations `gap * cadence + stall`, requires agreement across positive stalls, and checks zero-stall convergence consistency.

Reviewer reproduction after the fix:

```text
$ python3 - <<'PY'
from tests import test_search_model_candidate_sim as t
field = t.solve_latency_field(t.t12_matched_control_observations(
    [(0, 3), (1, 1), (2, 0), (3, 0)],
    [(0, 0), (1, 0), (2, 0), (3, 0)],
    cadence=2,
))
print(field['status'], field.get('value'))
print(field['t12_latency_constraints'][0]['reason'])
PY
exact_fit 3
T12 matched_control_convergence;...;stalls=[3, 1, 0, 0];...;converged_gap=2;positive_stall_latency=3;exact_latency=3
```

Regression coverage also includes a cadence-2 positive-stall disagreement case, which now fails closed as `non_identifiable`. The real-platform `/tmp` search output remains byte-for-byte identical to `results/common/search_model_real_platform.json`, so the checked-in real artifacts did not need regeneration.

### Accepted: Humanize2 control-plane ownership is fixed

The replay write-scope issue found during review is now fixed in the Round 13
capture update. Worker prompts/contracts, cartridge agent nodes, and
`h2_primitives.yaml` worker `owned_write_set` entries no longer grant
`.humanize/rlcr/**` write scope.

Ownership is now explicit:

- `.humanize/rlcr/2026-05-23_01-15-03/round-10-summary.md` is
  coordinator-owned.
- `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md` and
  `.humanize/rlcr/2026-05-23_01-15-03/round-10-review-result.md` are
  Codex-reviewer-owned.
- `results/common/agentic_flow/artifacts/decisions/round-13-control-plane-ownership.md`
  records the policy.

References to `.humanize/rlcr/**` remain allowed as read-only lineage evidence.

### HIGH 1. Formula-fit summaries overclaim exact formulas from partial LMUL evidence

`scripts/search_model_impl.py:1318-1343` builds formula fits from any field rows whose status is `exact_fit`. It does not check whether another required LMUL row for that same instruction/field is blocked. As a result, the current search artifact reports complete-looking exact formulas from partial LMUL coverage:

- `results/common/search_model_real_platform_summary.md:63-67` marks `vcpop_m` m4 `ReleaseAtCycles` non-identifiable, but `results/common/search_model_real_platform_summary.md:195-196` reports `vcpop_m` `ReleaseAtCycles` as `exact_fit` using only m1/m2 points.
- `results/common/search_model_real_platform_summary.md:153` marks `vrgather_vv` m4 `Latency` non-identifiable, but `results/common/search_model_real_platform_summary.md:207` reports `vrgather_vv` `Latency` as `exact_fit`.
- `results/common/search_model_real_platform_summary.md:168` marks `vslideup_vx` m4 `Latency` non-identifiable, but `results/common/search_model_real_platform_summary.md:209` reports `vslideup_vx` `Latency` as `exact_fit`.

Reviewer probe:

```text
vcpop_m ReleaseAtCycles fit_status= exact_fit fit_points= {'m1': 1, 'm2': 1} blocked_lmuls= ['m4']
vrgather_vv Latency fit_status= exact_fit fit_points= {'m1': 4, 'm2': 4} blocked_lmuls= ['m4']
vslideup_vx Latency fit_status= exact_fit fit_points= {'m1': 4, 'm2': 4} blocked_lmuls= ['m4']
```

Risk: AC-9 requires rule inference plus parameter-search consistency checks. A formula table that says `exact_fit` while a required LMUL point is explicitly `non_identifiable` is not an honest LLVM-facing confidence report. It also creates a future AC-16 hazard: a human approval or LLVM export could consume a formula that looks complete while its m4 basis is still approval-bound.

Required implementation plan:

1. Change `formula_fit_for()` to receive the required LMUL set for the first matrix (`m1`, `m2`, `m4`) plus the source field statuses.
2. If any required LMUL row for that field is not `exact_fit`, emit a non-complete status such as `partial_fit_blocked` or `insufficient_evidence`, include `blocked_lmuls` with the source statuses, and do not present the formula as a complete exact fit. It is acceptable to keep `points` and a provisional formula under a clearly named diagnostic key, but not as the primary claimed fit.
3. Add focused regression tests covering `vcpop_m` `ReleaseAtCycles` with exact m1/m2 plus blocked m4, and `vrgather_vv`/`vslideup_vx` `Latency` with exact m1/m2 plus blocked m4.
4. Regenerate `results/common/search_model_real_platform.json`, `results/common/search_model_real_platform_summary.md`, profile sidecars if affected, `real_platform_field_status.json`, `real_platform_inventory.json`, `experiment_quality.md`, and `real_platform_risk_acceptance_request.json`; refresh Humanize2 capture for the formula-fit repair.
5. Verify search byte-reproducibility, synthetic gate pass, real gate fail-closed for only legitimate remaining blockers, and `pytest`.

### Accepted: formula-fit coverage guard is fixed

The formula-fit issue above is now resolved in the current worktree. `formula_fit_for()` requires all required LMUL rows (`m1`, `m2`, and `m4`) to be exact before the primary formula status can be `exact_fit`. Missing or non-exact required rows now produce `partial_fit_blocked` and include `blocked_lmuls`; any exact subset fit is available only as `provisional_fit`.

Current checked-in search output now reports:

```text
vcpop_m ReleaseAtCycles -> partial_fit_blocked, blocked_lmuls=[m4]
vrgather_vv Latency -> partial_fit_blocked, blocked_lmuls=[m4]
vslideup_vx Latency -> partial_fit_blocked, blocked_lmuls=[m4]
```

The field-status counts are unchanged at 141 inferred and 9 `non_identifiable`; this repair changes formula confidence reporting and the search artifact hash, not the underlying real-platform evidence.

### BLOCKER 1. AC-16 remains incomplete

The original plan requires the real Paladin/platform flow to stop only on coverage, stability, confidence, documented assumptions, and explicit human approval before LLVM implementation. Current artifacts still fail closed:

- `results/common/experiment_quality.md:3-13`: `Gate status: NOT_READY`, confidence is `unresolved_llvm_field_status`, human approval is absent, and there are 9 unresolved risks.
- `results/common/experiment_quality.md:3863-3866`: failed checks are `required_llvm_field_status_clean_or_accepted` and `explicit_human_approval`.
- `results/common/experiment_quality.md:3877-3880`: 141 inferred rows and 9 `non_identifiable` rows.
- `results/common/experiment_quality.md:3886-3894`: the remaining 9 risk IDs are approval-bound.
- `results/common/experiment_quality.md:3916-3919`: no approval artifact exists, so the real gate cannot pass.

Reviewer reproduction:

```text
$ python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
FAIL: real_platform_profile gate did not pass using results/common/experiment_quality.md
- quality report must contain exact line `Gate status: PASS`
- missing machine-readable human approval file under results/common
- results/common/real_platform_inventory.json: unresolved real-platform LLVM field-status risks=9 status_counts={"non_identifiable": 9}
```

Remaining rows:

- 5 upper-bound-only Latency rows: `vcpop_m` m1/m2/m4, `vrgather_vv` m4, and `vslideup_vx` m4.
- 4 `vcpop_m` m4 non-affine issue/resource rows: `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue`.

Required implementation plan:

1. Do not create `results/common/human_approval.json` unless the human owner supplies explicit approval tied to the current hashes and exact accepted risk IDs.
2. If pursuing stronger evidence instead of approval, finish the matched T12 dependent-vs-control analysis for the 5 Latency rows and claim exact latency only when the dependent/control convergence point is discriminating and stable.
3. For the 4 `vcpop_m` m4 rows, implement one explicit model that explains all repeated T10/T21/R11 diagnostics, with tests and profile evidence. If the model is still falsified, keep the rows `non_identifiable`.
4. Regenerate search/profile/inventory/quality/request artifacts, verify byte-for-byte search reproducibility, run synthetic and real gates, and do not claim completion until the real-platform gate passes.

## Part 2: Goal Alignment Check

AC status at current HEAD/worktree:

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
| AC-9 | MET |
| AC-10 | MET |
| AC-11 | MET |
| AC-12 | MET |
| AC-13 | MET |
| AC-14 | MET |
| AC-15 | MET for the synthetic-gated LLVM path |
| AC-16 | NOT MET |
| AC-17 | MET |

Forgotten items found: none after the current-head capture refresh and formula-fit guard repair. No items are listed under Explicitly Deferred.

Goal Alignment Summary:

```text
ACs: 17/17 addressed, 16/17 met | Forgotten items: 0 | Unjustified deferrals: 0
```

## Part 3: Goal Tracker Update Requests

Claude's Round 10 tracker request is approved as a progress update, not a completion update.

Changes applied to `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`:

- Updated Plan Version to 24 for current-head formula-fit coverage repair.
- Kept the Round 10 progress entries for `f3bb4552`, `cd71b7ed`, `c1032a2c`, `73b99c2e`, and `7a7da5d2`.
- Kept the current-head search reproducibility fix entry for `8ec7a8a8`.
- Added a current-head capture verification entry for `77d181af`, `6ff16b7c`, `88c9e6e5`, and `8ec7a8a8`.
- Marked T6 and T12 completed for current-head Humanize2 capture/replay after parse checks and ownership grep checks passed.
- Marked T10 completed again because formula-fit summaries now fail closed as `partial_fit_blocked` whenever any required LMUL row is not exact.
- Kept T9 and T11 as `needs_changes` because AC-16 still lacks either explicit current-hash-bound human approval or stronger evidence resolving the 9 risks.
- Removed the now-resolved open issue for missing current-head Humanize2 capture.
- Removed the now-resolved AC-9 open issue for partial-LMUL formula fits reported as exact despite required blocked LMUL rows.
- Kept the open AC-16 issue for 9 non-identifiable real-platform LLVM-facing rows.
- Removed the resolved AC-9 issue for matched-control T12 exact-latency overclaim.
- Recorded the Round 13 control-plane ownership decision and the Round 14 formula-fit coverage decision.
- Did not modify the immutable goal or acceptance criteria section.

## Reviewer Verification Commands

- Formula-fit regression tests for blocked m4 rows and complete m1/m2/m4 fits: passed.
- `python3 -m pytest -q`: passed.
- `python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing PASS, missing approval, and 9 unresolved risks.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-formula-fit-search.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-formula-fit-search.json results/common/search_model_real_platform.json`: passed.
- Formula-fit probe reports `partial_fit_blocked` with blocked `m4` for `vcpop_m` `ReleaseAtCycles`, `vrgather_vv` `Latency`, and `vslideup_vx` `Latency`.
- Adversarial matched-control probe now reports `exact_fit 3` for cadence-2 stalls `[3, 1, 0, 0]`.
- YAML/JSON/JSONL/HTML parse for `results/common/agentic_flow/h2_primitives.yaml`, boards, tool-call JSON, request JSON, events, and cartridge: passed.
- Ownership grep check confirmed no worker prompt/contract or worker `owned_write_set` grants `.humanize/rlcr/**` write scope.
- Request risk IDs match inventory unresolved risk IDs exactly.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no output.
- `git diff --check` and `git diff --cached --check`: passed during review.

REQUEST CHANGES
