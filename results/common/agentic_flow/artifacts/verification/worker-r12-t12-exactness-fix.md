# Verification: Round 12 T12 Exactness Fix

Commands run:

- `python3 -m unittest tests.test_search_model_candidate_sim.SearchModelCandidateSimulatorTest.test_t12_matched_control_convergence_infers_exact_latency tests.test_search_model_candidate_sim.SearchModelCandidateSimulatorTest.test_t12_matched_control_partial_stalls_infer_sub_cadence_latency tests.test_search_model_candidate_sim.SearchModelCandidateSimulatorTest.test_t12_matched_control_disagreeing_positive_stalls_fail_closed`: passed.
- Adversarial probe for cadence-2 stalls `[3, 1, 0, 0]`: returned `exact_fit 3`.
- `python3 -m pytest -q`: passed, 56 tests.
- `python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results --mismatch-report results/common/mismatch_report.md`: passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-t12-fix-search.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-t12-fix-search.json results/common/search_model_real_platform.json`: passed.
- `sha256sum /tmp/profile-inst-latency-t12-fix-search.json results/common/search_model_real_platform.json`: both files had `2f3b78ebfd2e499bcd2420a9052e361fa63320ba801c7a155638b83d1975d6b6`.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing `Gate status: PASS`, missing machine-readable approval, and 9 unresolved `non_identifiable` rows.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no output.
