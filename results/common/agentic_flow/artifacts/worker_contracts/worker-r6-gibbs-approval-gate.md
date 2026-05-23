# Worker Contract: Round 6 Approval-Gate Hardening

Round: 6
Worker: Gibbs
Capture type: normalized reconstruction
Commit: `ea7c0acaa5d144ffd8aa5bb0ac3f8f17b8b156ac`
Review status: approval-gate code behavior accepted; capture gap found

This contract was added after Round 6 review found the approval-gate worker
capture missing. It records the durable contract implied by the Round 6
summary, review, and commit; it is not a verbatim prompt transcript.

## Objectives

- Treat `non_identifiable` real-platform field-status rows as unresolved
  approval-bound risks.
- Require approval to bind the current inventory hash and the current
  real-platform field-status hash.
- Require approval to include explicit accepted risk IDs or all-risk
  acceptance for unresolved field-status risks.
- Add focused regression tests for stale hashes, missing hashes, missing risk
  scope, and valid all-risk acceptance.
- Regenerate the inventory and quality artifacts from the checked-in
  real-platform state.
- Keep approval explicit and absent: do not create or imply a
  `results/common/*approval*` artifact.

## Owned Write Set

- `scripts/analyze.py`
- `scripts/check_calibration_gate.py`
- `tests/test_check_calibration_gate_approval.py`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`

## Forbidden Write Set

- `.humanize/**`
- `results/common/*approval*`
- unrelated script, test, result, or capture paths outside the assigned
  approval-gate hardening and regenerated-artifact scope.

## Required Validation

```bash
python3 -m unittest tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval
python3 -m pytest -q
python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r6-approval-search.json --format json
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
python3 -m json.tool results/common/real_platform_inventory.json >/dev/null
python3 -m json.tool /tmp/profile-inst-latency-r6-approval-search.json >/dev/null
find results/common -maxdepth 1 -iname '*approval*' -print
sha256sum results/common/real_platform_inventory.json results/common/real_platform_field_status.json results/common/search_model_real_platform.json results/common/experiment_quality.md
git diff --check
```

The real-platform gate command is expected to return nonzero until explicit
machine-readable human approval exists, covers the 39 unresolved field-status
risks, binds the current inventory and field-status hashes, and the quality
report contains `Gate status: PASS`.
