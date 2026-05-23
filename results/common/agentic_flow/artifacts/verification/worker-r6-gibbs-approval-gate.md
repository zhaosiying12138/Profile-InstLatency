# Verification: Round 6 Approval-Gate Worker Gibbs

Round: 6
Worker: Gibbs
Capture type: normalized reconstruction
Status: approval-gate behavior accepted by Round 6 review

This verification report combines evidence from commit
`ea7c0acaa5d144ffd8aa5bb0ac3f8f17b8b156ac`, the Round 6 summary, and the
Round 6 review result. It records the commands and outcomes needed for
empty-context replay; it is not a transcript of the original shell session.

## Commands Reported or Reproduced

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

Round 6 review additionally reproduced:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r6-review-search.json --format json
cmp /tmp/profile-inst-latency-r6-review-search.json results/common/search_model_real_platform.json
```

## Results

- `python3 -m unittest tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval`:
  passed, 17 tests.
- `python3 -m pytest -q`: passed, 17 tests in the Round 6 runs.
- `py_compile` for the core scripts passed.
- Real-platform search regeneration to a temporary output completed, and the
  reviewer reproduced a byte-for-byte match against
  `results/common/search_model_real_platform.json`.
- JSON validation passed for the inventory artifact and temporary real-platform
  search output.
- Synthetic calibration gate passed.
- Real-platform gate failed closed as expected because `Gate status: PASS`,
  a machine-readable approval artifact, and accepted scope for 39 unresolved
  field-status risks are absent.
- `find results/common -maxdepth 1 -iname '*approval*' -print` returned no
  paths.
- `git diff --check` passed for the Round 6 approval-gate commit.

## Current Round 6 Hashes

- `results/common/real_platform_inventory.json`:
  `4f25f066db09e0212200d48a181fd582e685701c16d18ca045dbc4738e4fb54b`
- `results/common/real_platform_field_status.json`:
  `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`
- `results/common/search_model_real_platform.json`:
  `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73`
- `results/common/experiment_quality.md`:
  `b6b6b1dde2095c59b43b702cfc53ec075b45982a2ff6ea0ee9fba12ab30bb5f6`

## Review Boundary

The Round 6 review accepted the approval-gate behavior, but the workflow
remains blocked on this missing Humanize2 capture package and on AC-16's
explicit approval or stronger-evidence requirement. This artifact does not mark
AC-16 complete.
