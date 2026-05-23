# Worker Contract: Round 5 Candidate-Simulator Code Worker

Round: 5
Worker: Anscombe
Capture type: normalized reconstruction
Commit: `773f27d67e8306ec8fbafc434dcd158953e71e95`
Review status: accepted for candidate-simulator scope

This contract was added after Round 5 review found the code-worker capture
missing. It records the durable contract implied by the Round 5 summary,
review, and commit; it is not a verbatim prompt transcript.

## Objectives

- Mirror T20 pair observations into existing peer rows so peer-only rows are
  constrained by the same startup-slope evidence as trace-owner rows.
- Require enough post-transition T12 coverage before a clean-prefix observation
  may produce an exact latency.
- Add regression tests proving both behaviors.
- Regenerate real-platform artifacts from the checked-in trace corpus.
- Keep approval explicit and absent: do not create or imply a
  `results/common/*approval*` artifact.

## Owned Write Set

- `scripts/search_model.py`
- `tests/test_search_model_candidate_sim.py`
- `results/common/search_model_real_platform.json`
- `results/common/search_model_real_platform_summary.md`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/vredsum_vs/profile.real_platform.yaml`

## Forbidden Write Set

- `.humanize/**`
- `results/common/*approval*`
- unrelated script, test, result, or capture paths outside the assigned
  candidate-simulator and regenerated-artifact scope.

## Required Validation

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

The real-platform gate command is expected to return nonzero until explicit
machine-readable human approval exists and the quality report contains
`Gate status: PASS`.
