# Round 10 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Scope note: I read `docs/plan.md`, the Round 10 prompt, and the goal tracker before reviewing. The strict Round 10 summary is accurate for commits through `7a7da5d2`: it added focused T20/T12 evidence, refreshed real-platform artifacts, reduced unresolved rows from 39 to 38, and kept the request pending rather than approved. Current `HEAD` is no longer exactly that boundary: after the committed Round 10 review (`190e8727`), commits `77d181af`, `6ff16b7c`, and `88c9e6e5` further changed the live artifacts to 141 inferred rows and 9 `non_identifiable` rows. This current-head audit also found that the checked-in search artifact is not byte-reproducible from the documented command.

## Part 1: Implementation Review

### Accepted: Round 10 focused-evidence claims were real

The Round 10 code/data commits named in Claude's summary exist and match the described direction:

- `f3bb455245cce28b1f61fd7447e1056e5c9903b2`: T20 m4 no-reuse ProcResource evidence and global resource solving support.
- `cd71b7ed3aa9d222306af23a51fe87efd76eddf9`: targeted `run_suite.py` filters.
- `c1032a2c01949ecb9d651473dec1aa88695bb484`: focused T12 scalar-filler evidence.
- `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`: focused real gem5 refresh and regenerated artifacts.
- `7a7da5d2`: Round 10 Humanize2 capture and summary.

At that boundary, the 39 to 38 risk reduction was valid progress, not completion.

### Accepted with scope caveat: current request semantics remain safe

Current `results/common/real_platform_risk_acceptance_request.json:4-14` is now a Round 11 request, but it remains safe: pending, not approved, not submitted, not a gate input, not an approval artifact, and not gate-consumed. Its current hashes are listed at `results/common/real_platform_risk_acceptance_request.json:17-21`, and the 9 risk IDs at `results/common/real_platform_risk_acceptance_request.json:30-39` match the inventory unresolved list. `find results/common -maxdepth 1 -iname '*approval*' -print` produced no output.

### BLOCKER 1. AC-16 remains incomplete at current HEAD

The original plan requires real-platform profiling to stop only on coverage, stability, confidence, documented assumptions, and explicit human approval before LLVM implementation (`docs/plan.md`, AC-16). Current artifacts still fail closed:

- `results/common/experiment_quality.md:3-13`: `Gate status: NOT_READY`, confidence is `unresolved_llvm_field_status`, human approval is absent, and there are 9 unresolved risks.
- `results/common/experiment_quality.md:3863-3866`: failed checks are `required_llvm_field_status_clean_or_accepted` and `explicit_human_approval`.
- `results/common/experiment_quality.md:3877-3880`: 141 inferred rows and 9 `non_identifiable` rows.
- `results/common/experiment_quality.md:3886-3894`: the remaining 9 risk IDs are still approval-bound.
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
2. For the 5 Latency rows, finish the matched T12 dependent-vs-control analysis so exact latency is claimed only when the dependent/control convergence point is discriminating and stable. If the evidence remains only an upper bound, keep the row `non_identifiable` and require human approval.
3. For the 4 `vcpop_m` m4 rows, either implement one explicit model that explains all repeated T10/T21/R11 diagnostics, with tests and profile evidence, or keep the rows `non_identifiable` and require human approval. Do not invent LLVM-facing values from the falsified diagnostics.
4. Regenerate search/profile/inventory/quality/request artifacts, verify byte-for-byte search reproducibility, run the synthetic gate, and require the real-platform gate to pass before any completion claim.

### BLOCKER 2. Current search artifact is not byte-reproducible

Claude's summary and the existing Round 10 review both rely on the real-platform search artifact being reproducible from the captured command. At current `HEAD`, that is false. After restoring the unintended tracked-file side effect from my verification run, the regenerated `/tmp` output differs from the checked-in request-bound artifact:

```text
$ python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-current-review-search.json --format json
wrote /tmp/profile-inst-latency-current-review-search.json

$ cmp /tmp/profile-inst-latency-current-review-search.json results/common/search_model_real_platform.json
/tmp/profile-inst-latency-current-review-search.json results/common/search_model_real_platform.json differ: byte 330, line 17
```

Hashes:

- Checked-in/request-bound `results/common/search_model_real_platform.json`: `2f3b78ebfd2e499bcd2420a9052e361fa63320ba801c7a155638b83d1975d6b6`.
- Fresh regenerated `/tmp/profile-inst-latency-current-review-search.json`: `4984893d1db88d7b3640f38797e151aefc70651b6cb10f2bc08c8cc8d40a7559`.

The first observed semantic drift is `config_files_reference_only`: checked-in JSON contains `["config/rvv_timing_model.yaml"]`, while the regenerated output contains `[]`. If the canonical output path is used, the command rewrites tracked artifacts and changes the request-bound hash. This reopens AC-9 and blocks AC-16 because the current request is tied to a search artifact that the documented command does not reproduce.

Required implementation plan:

1. Fix the search regeneration path so the documented command reproduces the checked-in JSON byte-for-byte from a clean worktree, without mutating tracked files when a `/tmp` output path is requested.
2. If the regenerated form is the intended canonical form, regenerate `results/common/search_model_real_platform.json` and every dependent profile sidecar, field-status file, inventory, quality report, risk request, hash, and Humanize2 capture.
3. Add a regression test or verification script for this exact reproduction path.
4. Rerun `cmp` from a clean worktree before claiming the search artifact is reproducible.

### BLOCKER 3. Current-head Humanize2 capture is stale

Round 10 Humanize2 capture was valid for commit `7a7da5d2`, but current `HEAD` includes three later evidence commits. No `results/common/agentic_flow/**` or `.humanize` capture files changed after the Round 10 review commit:

```text
$ git diff --name-only 190e8727..HEAD -- .humanize results/common/agentic_flow
<no output>
```

Evidence of staleness:

- `results/common/real_platform_risk_acceptance_request.json:4-5` says the live request is Round 11 from `Round11VcpopM4IssueFieldDiagnostics`.
- `results/common/agentic_flow/boards/execution_state.yaml:14-88` still records Round 10, 38 unresolved rows, and the old hashes.
- `results/common/agentic_flow/cartridges/rvv-profile-workflow.draft.html:139-146` still records 38 unresolved risks and the Round 10 hashes.
- The goal tracker also still had the 38-risk Round 10 state before this review updated the mutable section.

This reopens AC-12 and AC-13 for current `HEAD`. Required implementation plan:

1. Add a current capture package under `results/common/agentic_flow/**` for commits `77d181af`, `6ff16b7c`, and `88c9e6e5`.
2. Save the prompts, worker contracts, worker outputs, verification artifacts, and normalized tool-call JSON for the post-Round 10 work.
3. Refresh boards, events, replay, status view, draft cartridge, manifest notes, and request-boundary metadata to the current 9-risk hashes.
4. Preserve request semantics: request only, not approval, not gate input, not gate-consumed.

## Part 2: Goal Alignment Check

AC status at current `HEAD`:

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
| AC-9 | NOT MET at current HEAD because the checked-in search artifact is not byte-reproducible from the documented command |
| AC-10 | MET |
| AC-11 | MET |
| AC-12 | NOT MET for current HEAD because post-Round 10 evidence is uncaptured |
| AC-13 | NOT MET for current HEAD because replay/cartridge still point to the Round 10 38-risk boundary |
| AC-14 | MET |
| AC-15 | MET for synthetic-gated LLVM path |
| AC-16 | NOT MET |
| AC-17 | MET |

Forgotten item found: post-Round 10 evidence capture was not tracked before this review. No items are listed under Explicitly Deferred. There are no justified deferrals that make the original plan complete.

Goal Alignment Summary:

```text
ACs: 17/17 addressed, 13/17 met | Forgotten items: 1 | Unjustified deferrals: 0
```

## Part 3: Goal Tracker Update Requests

Claude's Round 10 tracker request is approved as a progress update, not a completion update. I also updated the tracker for the current-head drift discovered during review.

Changes applied to `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`:

- Updated Plan Version to 16 for this current-head addendum.
- Kept the Round 10 Plan Evolution entry, and added a current-head addendum for commits `77d181af`, `6ff16b7c`, and `88c9e6e5`.
- Reopened T6 and T12 as `needs_changes` because `results/common/agentic_flow/**` is stale relative to current artifacts.
- Updated T9 and T11 notes to the current 141 inferred / 9 non-identifiable state and current hashes.
- Reopened T10 as `needs_changes` because regenerated search output differs from the checked-in request-bound artifact.
- Updated the open AC-16 issue from 38 to 9 unresolved rows.
- Added an open AC-12/AC-13 issue for missing current-head Humanize2 capture.
- Added an open AC-9/AC-16 issue for the search artifact reproducibility mismatch.
- Did not modify the immutable goal or acceptance criteria section.

## Reviewer Verification Commands

- `python3 -m pytest -q`: passed, 49 tests.
- `python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py`: passed.
- `git diff --check && git diff --cached --check`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing PASS, missing approval, and 9 unresolved risks.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-current-review-search.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-current-review-search.json results/common/search_model_real_platform.json`: failed at byte 330, line 17.
- `sha256sum` confirmed the current inventory, field-status, search, quality, and request hashes.
- Request risk IDs match inventory unresolved risk IDs exactly.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no output.

REQUEST CHANGES
