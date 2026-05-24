## Work Completed

- Fixed `[P2] Load profile contents before unpacking them` in `scripts/export_llvm_draft.py`.
- Fixed `[P2] Honor dry-run before launching gem5` in `scripts/run_experiment.py`.
- Fixed `[P2] Keep default reports under the selected root` in `scripts/analyze.py`.
- Added focused regression coverage in `tests/test_review_phase_round12.py`.

## How Each Issue Was Resolved

- `export_llvm_draft.load_profiles()` now pairs each discovered `profile.yaml` path with parsed profile contents before `build_rows()` unpacks rows.
- `run_experiment_from_metadata()` now handles `dry_run` before the gem5 backend branch, so explicit `--dry-run --backend gem5_minor --mode real_platform_profile` writes a synthetic dry-run trace and never launches gem5.
- `analyze.parse_args()` now derives default `--aggregate` and `--mismatch-report` paths from `--root`, while preserving explicit report paths.

## Validation

- `python3 -m unittest tests.test_review_phase_round12` passed.
- `python3 scripts/export_llvm_draft.py --profile-root results --td-output /tmp/profile-inst-latency-round12-draft.td --mapping-output /tmp/profile-inst-latency-round12-map.md` passed.
- `python3 scripts/run_experiment.py t01-vslideup-vx-m4 --dry-run --mode real_platform_profile --backend gem5_minor --results-root /tmp/profile-inst-latency-round12-dryrun` passed and produced `mode=dry_run`, `backend=synthetic_cmodel`, `dry_run_trace=True`.
- `python3 scripts/analyze.py --root /tmp/profile-inst-latency-round12-dryrun --dry-run` printed writes under `/tmp/profile-inst-latency-round12-dryrun/common`.
- `python3 -m py_compile scripts/approval_status.py scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/analyze_core.py scripts/analyze_quality.py scripts/run_experiment.py scripts/export_llvm_draft.py` passed.
- `python3 -m pytest -q` passed with 67 tests.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results` passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r12-search.json --format json && cmp /tmp/profile-inst-latency-r12-search.json results/common/search_model_real_platform.json` passed.
- `git diff --check` passed.

## Unresolved Issues

- None.

## BitLesson Selection

- `export_llvm_draft` profile-content fix: `LESSON_IDS: NONE`.
- `run_experiment` dry-run gem5 fix: `LESSON_IDS: NONE`.
- `analyze` selected-root report defaults fix: `LESSON_IDS: NONE`.

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: `.humanize/bitlesson.md` contains no concrete lesson entries, and all three required selector runs returned `NONE`.
