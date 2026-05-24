## Work Completed

- Fixed `[P2] Support block-list YAML approvals`.
- Fixed `[P2] Regenerate checked-in experiments with generator v3`.
- Added focused regression coverage for both findings.

## How Each Issue Was Resolved

- `scripts/check_calibration_gate.py` now parses simple YAML block lists, including `accepted_risk_ids:\n  - all`, so YAML approvals can carry the same accepted-risk scope as JSON approvals.
- `experiments/generated` was regenerated with `python3 scripts/gen_asm.py suite --output-root experiments/generated`; all checked-in `experiment.yaml` files now record `generator_version: 3`.
- `tests/test_check_calibration_gate_approval.py` now covers YAML block-list risk acceptance.
- `tests/test_generated_experiments_fresh.py` now checks checked-in generated experiment metadata against `scripts/gen_asm.py`'s current `GENERATOR_VERSION`.

## Validation

- `python3 -m unittest tests.test_check_calibration_gate_approval.ApprovalGateHardeningTest.test_yaml_block_list_risk_acceptance_passes_unresolved_field_status` passed.
- `python3 -m unittest tests.test_generated_experiments_fresh` passed.
- `grep -R "generator_version:" experiments/generated/*/experiment.yaml | cut -d: -f3 | sort | uniq -c` reports `3665  3`.
- `python3 scripts/gen_asm.py suite --output-root experiments/generated` passed and regenerated 3665 entries.
- `python3 -m py_compile scripts/approval_status.py scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/analyze_core.py scripts/analyze_quality.py scripts/run_experiment.py scripts/export_llvm_draft.py` passed.
- `python3 -m pytest -q` passed with 69 tests.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results` passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r13-search.json --format json && cmp /tmp/profile-inst-latency-r13-search.json results/common/search_model_real_platform.json` passed.
- `git diff --check` passed.

## Unresolved Issues

- None.

## BitLesson Selection

- YAML block-list approval fix: `LESSON_IDS: NONE`.
- Generated experiment v3 refresh: `LESSON_IDS: NONE`.

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: `.humanize/bitlesson.md` contains no concrete lesson entries, and both required selector runs returned `NONE`.
