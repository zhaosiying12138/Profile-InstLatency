# Verification: Round 16 Approval Discovery Scope

Commands and outcomes:

- `python3 -m unittest tests.test_check_calibration_gate_approval.ApprovalGateHardeningTest.test_nested_human_approval_is_not_discovered_or_gate_consumed`: failed before the fix because analyzer discovery reported the nested approval as approved.
- `python3 -m unittest tests.test_check_calibration_gate_approval.ApprovalGateHardeningTest.test_nested_human_approval_is_not_discovered_or_gate_consumed tests.test_check_calibration_gate_approval.ApprovalGateHardeningTest.test_human_approved_top_level_status_has_analyzer_gate_parity`: passed after the shared approval-file helper.
- `python3 -m unittest tests.test_check_calibration_gate_approval`: passed, 11 tests.
- `python3 -m py_compile scripts/approval_status.py scripts/check_calibration_gate.py scripts/analyze.py scripts/analyze_core.py scripts/analyze_quality.py`: passed.
- `git diff --check`: passed before the implementation commit.
- `python3 -m pytest -q`: passed, 63 tests.
- `python3 scripts/analyze.py --all --dry-run`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing `Gate status: PASS`, missing machine-readable approval, and 9 unresolved `non_identifiable` risks.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-approval-scope-search.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-approval-scope-search.json results/common/search_model_real_platform.json`: passed.
- `sha256sum /tmp/profile-inst-latency-approval-scope-search.json results/common/search_model_real_platform.json`: both files had SHA `3d72fd2e87b517e3e7ba3699eb214b8f35874055f3ed51c519aa4671d5f002bd`.

No approval artifact was created.
