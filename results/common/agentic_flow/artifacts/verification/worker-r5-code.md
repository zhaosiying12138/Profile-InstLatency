# Verification: Round 5 Candidate-Simulator Code Worker

Round: 5
Worker: Anscombe
Capture type: normalized reconstruction
Status: candidate-simulator scope accepted by Round 5 review

This verification report combines evidence from commit
`773f27d67e8306ec8fbafc434dcd158953e71e95`, the Round 5 summary, and the
Round 5 review result. It records the commands and outcomes needed for
empty-context replay; it is not a transcript of the original shell session.

## Commands Reported or Reproduced

```bash
python3 -m unittest tests.test_search_model_candidate_sim
python3 -m pytest -q
python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json
python3 scripts/analyze.py --all --root results
python3 -m json.tool results/common/search_model_real_platform.json >/dev/null
python3 -m json.tool results/common/real_platform_field_status.json >/dev/null
python3 -m json.tool results/common/real_platform_inventory.json >/dev/null
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
find results/common -maxdepth 1 -iname '*approval*' -print
sha256sum results/common/real_platform_inventory.json results/common/real_platform_field_status.json results/common/search_model_real_platform.json results/common/experiment_quality.md
git diff --check
```

Round 5 review additionally reproduced:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r5-review-search.json --format json
cmp /tmp/profile-inst-latency-r5-review-search.json results/common/search_model_real_platform.json
```

## Results

- `python3 -m unittest tests.test_search_model_candidate_sim`: passed, 10
  tests.
- `python3 -m pytest -q`: passed, 10 tests in the Round 5 review run.
- `py_compile` for the core scripts passed.
- Real-platform search regeneration completed and the reviewer reproduced a
  byte-for-byte match against `results/common/search_model_real_platform.json`.
- JSON validation passed for real-platform search, field-status, and inventory
  artifacts.
- `vredsum_vs` has T20 peer-side groups in the regenerated search artifact for
  `m1`, `m2`, and `m4`.
- Field-status count remained 150 rows: 111 `inferred`, 39
  `non_identifiable`, 0 `conflict`, and 0 `insufficient_evidence`.
- Synthetic calibration gate passed.
- Real-platform gate failed closed as expected because `Gate status: PASS` and
  a machine-readable approval artifact are absent.
- `find results/common -maxdepth 1 -iname '*approval*' -print` returned no
  paths.
- `git diff --check` passed for the Round 5 code-worker commit.

## Current Hashes

- `results/common/real_platform_inventory.json`:
  `d29e632b98c0a5734d541939c561872eeed691fd3c00b7ea83cf8aea666a536d`
- `results/common/real_platform_field_status.json`:
  `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`
- `results/common/search_model_real_platform.json`:
  `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73`
- `results/common/experiment_quality.md`:
  `6062c76f6f051eac6c60b0ead3be0e8ac74bc3f723841a0ec19d0d7a750e7307`

## Review Boundary

The Round 5 review accepted the code-worker candidate-simulator fixes, but the
workflow remains blocked on capture completeness before this package and on
AC-16 approval hardening plus absent explicit approval. This artifact does not
mark AC-16 complete.
