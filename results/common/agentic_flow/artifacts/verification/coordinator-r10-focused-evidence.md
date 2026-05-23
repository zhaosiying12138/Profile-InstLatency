# Verification: Coordinator Round 10 Focused Evidence

Round: 10
Owner: RLCR coordinator
Status: source evidence captured from committed Round 10 work

## Commands Captured

```bash
python3 scripts/run_suite.py --all --generated-root experiments/generated --results-root results --template-id T20_PAIRWISE_PIPE_CLASSIFICATION --id-regex 'resource-noreuse$' --missing --repeat 2 --mode real_platform_profile --backend gem5_minor
python3 scripts/run_suite.py --all --generated-root experiments/generated --results-root results --template-id T12_CONSUMER_RAW_GAP --id-regex 'fscalar-add$' --missing --repeat 2 --mode real_platform_profile --backend gem5_minor
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json
python3 scripts/analyze.py --all --root results --aggregate results/common/experiment_quality.md --mismatch-report results/common/mismatch_report.md --inventory results/common/real_platform_inventory.json
python3 -m unittest tests.test_run_suite_selection tests.test_gen_asm_t20_coverage tests.test_gen_asm_t12_focused tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval
python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py
python3 -m pytest -q
git diff --check
git diff --cached --check
```

## Results Captured

- Incremental real gem5 was run for 108 T20 resource-noreuse experiments and
  54 T12 scalar-filler experiments with repeat 2.
- Unit test command passed with 33 tests.
- `py_compile` passed for the listed scripts.
- `pytest -q` passed with 33 tests.
- `git diff --check` and `git diff --cached --check` passed before commit
  `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`.
- Synthetic gate passed.
- Real gate failed closed as expected on missing machine-readable human
  approval and 38 unresolved `non_identifiable` risks.
- No `results/common/human_approval.*` artifact exists.
