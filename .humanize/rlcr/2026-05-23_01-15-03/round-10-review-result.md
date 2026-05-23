# Round 10 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Scope note: I read `docs/plan.md`, `.humanize/rlcr/2026-05-23_01-15-03/round-10-prompt.md`, and `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md` before reviewing. The strict Round 10 summary is accurate for commits through `7a7da5d2`: Round 10 added focused T20/T12 evidence, refreshed real-platform artifacts, reduced unresolved rows from 39 to 38, and kept the request pending rather than approved. Current `HEAD` is now past that boundary and includes `77d181af`, `6ff16b7c`, `88c9e6e5`, `8ec7a8a8`, `fbc490b4`, and `91201d20`; current artifacts report 141 inferred rows and 9 `non_identifiable` rows.

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

Forgotten items found: none after the current-head capture refresh. No items are listed under Explicitly Deferred. There are no justified deferrals that make the original plan complete.

Goal Alignment Summary:

```text
ACs: 17/17 addressed, 16/17 met | Forgotten items: 0 | Unjustified deferrals: 0
```

## Part 3: Goal Tracker Update Requests

Claude's Round 10 tracker request is approved as a progress update, not a completion update.

Changes applied to `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`:

- Updated Plan Version to 20 for current-head capture verification plus the matched-control T12 exactness fix.
- Kept the Round 10 progress entries for `f3bb4552`, `cd71b7ed`, `c1032a2c`, `73b99c2e`, and `7a7da5d2`.
- Kept the current-head search reproducibility fix entry for `8ec7a8a8`.
- Added a current-head capture verification entry for `77d181af`, `6ff16b7c`, `88c9e6e5`, and `8ec7a8a8`.
- Marked T6 and T12 completed for current-head Humanize2 capture/replay after parse checks passed.
- Marked T10 completed again after `91201d20` fixed matched-control exactness and tests/search byte-repro passed.
- Kept T9 and T11 as `needs_changes` because AC-16 still lacks either explicit current-hash-bound human approval or stronger evidence resolving the 9 risks.
- Removed the now-resolved open issue for missing current-head Humanize2 capture.
- Kept the open AC-16 issue for 9 non-identifiable real-platform LLVM-facing rows.
- Removed the resolved AC-9 issue for matched-control T12 exact-latency overclaim.
- Did not modify the immutable goal or acceptance criteria section.

## Reviewer Verification Commands

- `python3 -m pytest -q`: passed, 56 tests.
- `python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing PASS, missing approval, and 9 unresolved risks.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r10-review-current-search.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-r10-review-current-search.json results/common/search_model_real_platform.json`: passed.
- Adversarial matched-control probe now reports `exact_fit 3` for cadence-2 stalls `[3, 1, 0, 0]`.
- YAML/JSON/JSONL parse for `results/common/agentic_flow/h2_primitives.yaml`, boards, tool-call JSON, request JSON, and `events.jsonl`: passed.
- Request risk IDs match inventory unresolved risk IDs exactly.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no output.
- `git diff --check` and `git diff --cached --check`: passed during review.

REQUEST CHANGES
