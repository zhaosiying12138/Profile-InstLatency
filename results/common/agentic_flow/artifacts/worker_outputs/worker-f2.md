# Worker F2 Report

## Changed Paths

- `scripts/analyze.py`
- `scripts/search_model.py`
- `scripts/check_calibration_gate.py`
- `scripts/export_llvm_draft.py`
- `results/<instruction>/profile.yaml` for all 10 RVV instructions
- `results/**/experiments/**/analysis.md` generated from available traces
- `results/common/mismatch_report.md`
- `results/common/experiment_quality.md`
- `results/common/llvm_model_draft.td`
- `results/common/llvm_model_mapping.md`

## Commands Run

- `python3 -m py_compile scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py scripts/export_llvm_draft.py`
- `python3 scripts/analyze.py --all`
- `python3 scripts/search_model.py --profile results --format json --output /tmp/f2-search.json`
- `python3 scripts/export_llvm_draft.py`
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration`
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile`

## Results

- Analyzer consumed 407 trace files and generated 407 experiment analysis reports.
- Profiles exist for all 10 configured instructions with `measurements.m1`, `measurements.m2`, and `measurements.m4`.
- Synthetic latency, release, pipe affinity, and resource-group claims match `config/rvv_timing_model.yaml`.
- Parameter search reads `profile.yaml` and found exact zero-residual `base_plus_lmul_times_k` fits for latency and release.
- LLVM draft export now uses profile evidence for per-LMUL latency, release, and resource values.
- Synthetic calibration gate passed.
- Real-platform profile gate failed as expected because the report is `NOT_READY` and has no explicit human approval.

## Caveats

- `NumMicroOps`, `SingleIssue`, `ReadAdvance`, and physical writeback latency are recorded but unclaimed because current synthetic evidence does not identify them.
- `OMX_TEAM_WORKER` was not set in this shell, so mailbox ACK/claim protocol could not be performed.
- Other workers have concurrent edits in generated inputs, runner files, docs, and agentic-flow state; this commit stages only Worker F2-owned files.
