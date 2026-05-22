# Worker F1 Report

## Changed Paths

- `scripts/gen_asm.py`
- `scripts/run_experiment.py`
- `scripts/run_suite.py`
- `templates/rvv_program.s.tpl`
- `experiments/generated/**`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-f1.md`

## Summary

- Normalized generated and result `experiment.yaml` files to expose top-level `experiment_id`, `template_id`, `result_group`, `instruction_id`, `lmul`, `sew`, and `markers`, while preserving nested metadata.
- Materialized the full generated suite using canonical lowercase generator IDs: T00, all T01/T10/T11/T12/T20/T21/T30 entries, plus T40 common load-hit.
- Updated the runner to accept generated experiment directories directly, copy generated `test.s` into result directories, and emit deterministic synthetic traces in `synthetic_calibration` mode without requiring gem5.
- Kept `--dry-run` as a labeled scaffold mode and made `real_platform_profile` fail closed with an actionable no-real-backend message.
- Updated `run_suite.py` to execute from `experiments/generated/suite_manifest.yaml`; `--killcheck` selects only T01 entries and `--all` selects the full manifest.

## Verification

- `python3 -m py_compile scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py`
- `python3 scripts/gen_asm.py suite`
  - `entry_count: 377`
  - `generated_count: 377`
- `python3 scripts/run_experiment.py experiments/generated/t01-vadd-vv-m1 --dry-run --results-root /tmp/f1-one-dry`
  - wrote `/tmp/f1-one-dry/common/experiments/t01-vadd-vv-m1`
  - generated `test.s` matches `experiments/generated/t01-vadd-vv-m1/test.s`
- `python3 scripts/run_suite.py --killcheck --results-root /tmp/f1-killcheck`
  - trace count: 30
  - non-T01 trace count: 0
- `python3 scripts/run_suite.py --all --results-root /tmp/f1-all`
  - total trace count: 377
  - T12 trace count: 30
  - T20 trace count: 135
  - T21 trace count: 30
  - T40 trace count: 1
  - top-level result groups: `common`, `vadd_vv`, `vcpop_m`, `vdivu_vv`, `viota_m`, `vmseq_vv`, `vmul_vv`, `vredsum_vs`, `vrgather_vv`, `vslideup_vx`, `vsll_vv`
- `python3 scripts/run_experiment.py experiments/generated/t01-vadd-vv-m1 --mode real_platform_profile --results-root /tmp/f1-real-profile`
  - exits 2 with a no-real-backend message, as intended.
- `find /tmp/f1-one-dry /tmp/f1-killcheck /tmp/f1-all \( -name profile.yaml -o -name analysis.md \) -print | wc -l`
  - result: 0

## Caveats

- T40 is included as a common synthetic load-hit scaffold. `config/rvv_timing_model.yaml` has no dedicated load timing entry, so the T40 trace records `timing_model_entry_found: false` and uses the runner's deterministic default latency/release values.
- Several non-F1 files already have concurrent modifications in the worktree. They were not edited for this report and should not be attributed to Worker F1.
