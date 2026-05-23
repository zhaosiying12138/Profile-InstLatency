# Worker G3-C Notes

## Scope

- Owned file: `scripts/search_model.py`
- Notes artifact: `results/common/agentic_flow/artifacts/worker_outputs/worker-g3-c.md`

## BitLesson

- Selector command: `bitlesson-selector --task "Worker G3-C: fix search_model T11 latency routing T12 non-identifiable handling T20 resource modeling and executable follow-ups" --paths "scripts/search_model.py,results/common/search_model_real_platform.json,results/common/search_model_real_platform_summary.md,results/common/real_platform_field_status.json,results/common/real_platform_inventory.json,results/common/experiment_quality.md,results/*/profile.real_platform.yaml,results/common/agentic_flow/artifacts/worker_outputs/worker-g3-c.md" --bitlesson-file .humanize/bitlesson.md`
- Result: `LESSON_IDS: NONE`
- Rationale: `.humanize/bitlesson.md` has no lesson entries.

## Changes

- T11 contributes latency constraints only when `body.latency_evidence`, `body.true_raw_chain`, or `body.chainable` is true.
- Non-chainable latency rows are reported as non-identifiable instead of exact-fit latency when only placeholder T11/T12 evidence exists.
- T20 observations are recorded as startup+slope groups without requiring `delta % pair_count == 0`; single-count real traces keep `ProcResource` non-identifiable with an executable pair-count sweep follow-up.
- Field-status rows now include follow-up text for `non_identifiable` rows.

## Validation

- `python3 -m py_compile scripts/search_model.py`: passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search.json --format json`: passed.
- `python3 -m json.tool /tmp/profile-inst-latency-real-search.json >/dev/null`: passed.
