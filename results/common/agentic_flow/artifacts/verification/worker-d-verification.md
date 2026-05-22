# Verification: Worker D Backfill

Worker: D
Round: 0
Status: backfilled from `artifacts/worker_outputs/worker-d.md`

## Recorded Commands

```bash
python3 -m py_compile scripts/run_experiment.py scripts/run_suite.py scripts/run_killcheck.py
python3 scripts/run_suite.py --killcheck --dry-run
python3 scripts/run_killcheck.py --dry-run
python3 -m json.tool results/common/experiments/T01_DECODE_EXEC_KILLCHECK-vadd_vv-m1/trace.json
python3 scripts/run_experiment.py results/common/experiments/T01_DECODE_EXEC_KILLCHECK-vadd_vv-m1 --dry-run --results-root /tmp/profile-inst-latency-runner-check
python3 scripts/run_suite.py --all --dry-run --results-root /tmp/profile-inst-latency-suite-all-check
```

## Caveat

These commands are preserved from Worker D's report and were not rerun by
Worker F3. They are dry-run scaffold checks, not real platform profiling proof.
