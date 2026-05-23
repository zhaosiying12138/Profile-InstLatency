# Round 11 Current-Head Capture Worker Prompt

Capture the post-Round-10 current-head state for empty-context replay.

Scope:

- Record commits `77d181af`, `6ff16b7c`, `88c9e6e5`, and `8ec7a8a8`.
- Refresh `results/common/agentic_flow/**` only.
- Preserve `results/common/real_platform_risk_acceptance_request.json` as a pending request, not an approval artifact.
- Do not create `results/common/human_approval.json`.

Required checks:

- `python3 -m pytest -q`
- `python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py`
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results --mismatch-report results/common/mismatch_report.md`
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` must fail closed on missing PASS, missing approval, and 9 unresolved `non_identifiable` rows.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-current-review-search-fixed.json --format json`
- `cmp /tmp/profile-inst-latency-current-review-search-fixed.json results/common/search_model_real_platform.json`
