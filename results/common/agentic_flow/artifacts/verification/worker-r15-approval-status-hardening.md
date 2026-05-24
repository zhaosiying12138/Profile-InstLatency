# Verification: Round 15 Approval-Status Hardening

Commands run:

- Red check for `test_human_approved_top_level_status_has_analyzer_gate_parity`:
  failed before the shared helper because analyzer discovery returned approved
  while gate validation returned false.
- `python3 -m unittest tests.test_check_calibration_gate_approval.ApprovalGateHardeningTest.test_human_approved_top_level_status_has_analyzer_gate_parity`:
  passed after the shared helper.
- `python3 -m unittest tests.test_check_calibration_gate_approval`: passed, 10
  tests.
- `python3 -m py_compile scripts/approval_status.py scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/analyze_core.py scripts/analyze_quality.py scripts/run_experiment.py`:
  passed.
- `python3 -m pytest -q`: passed, 62 tests.
- `python3 scripts/analyze.py --all --dry-run`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results --mismatch-report results/common/mismatch_report.md`:
  passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-round15-review-search.json --format json`:
  passed.
- `cmp /tmp/profile-inst-latency-round15-review-search.json results/common/search_model_real_platform.json`:
  passed.
- `sha256sum /tmp/profile-inst-latency-round15-review-search.json results/common/search_model_real_platform.json`:
  both files had
  `3d72fd2e87b517e3e7ba3699eb214b8f35874055f3ed51c519aa4671d5f002bd`.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`:
  failed closed as expected on missing `Gate status: PASS`, missing
  machine-readable approval, and 9 unresolved `non_identifiable` risks.
- YAML/JSON/JSONL parse and registered-path checks for
  `results/common/agentic_flow/**`: passed with 74 events.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no output.
- `git diff --check`: passed.
