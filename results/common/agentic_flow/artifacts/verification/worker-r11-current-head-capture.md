# Verification: Round 11 Current-Head Capture

Commands run:

- `python3 -m pytest -q`: passed, 54 tests.
- `python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results --mismatch-report results/common/mismatch_report.md`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed closed as expected on missing `Gate status: PASS`, missing machine-readable approval, and 9 unresolved `non_identifiable` rows.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-current-review-search-fixed.json --format json`: passed.
- `cmp /tmp/profile-inst-latency-current-review-search-fixed.json results/common/search_model_real_platform.json`: passed.
- `sha256sum /tmp/profile-inst-latency-current-review-search-fixed.json results/common/search_model_real_platform.json`: both files had `2f3b78ebfd2e499bcd2420a9052e361fa63320ba801c7a155638b83d1975d6b6`.
- Request hashes match current inventory, field-status, search, and quality artifacts.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: no output.

Current hashes:

- Inventory: `197787ab2389df7a059aa9221a70dc5c03c4a18f7dade0c605aca939faa671fd`
- Field status: `079cb94d27e98bdcf9df0ae0595a6e12b101e4c8c5a3d46f7d627dd4c81c1432`
- Search: `2f3b78ebfd2e499bcd2420a9052e361fa63320ba801c7a155638b83d1975d6b6`
- Quality: `d3c2e41f9bcd1a3b92ed2e148be5929d82a8ae111486c7471755030f7af1a31a`
