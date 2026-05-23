# Round 2 Summary

## Work Completed
- Implemented a shared real-platform candidate timing-model simulator in `scripts/search_model.py` for `Latency`, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue`.
- Replaced independent T10/T11 field equations with candidate-tuple checks over the observed marker bodies, using `startup + (N - 1) * field` for repeated throughput/RAW-chain observations.
- Integrated T12, T20, and T21 into the shared candidate path:
  - T12 observations are recorded as non-identifiable without an explicit bypass/read-advance model.
  - T20 observations are recorded as non-identifiable for current single pair-count templates when pipe identity cannot be separated from startup/overlap.
  - T21 scalar-pair observations are evaluated inside the same candidate tuple.
- Regenerated real-platform search, field-status, inventory, experiment-quality, and per-instruction `profile.real_platform.yaml` artifacts from the shared simulator.
- Reduced real-platform LLVM-facing unresolved field risks from 118 to 5. The remaining 5 conflicts are all for `vcpop_m` at LMUL `m4`, where the observed T10/T11 deltas do not fit any single candidate tuple.
- Kept the real-platform gate fail-closed. No human approval artifact was created.

## Files Changed
- `scripts/search_model.py`
- `results/common/search_model_real_platform.json`
- `results/common/search_model_real_platform_summary.md`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/vadd_vv/profile.real_platform.yaml`
- `results/vcpop_m/profile.real_platform.yaml`
- `results/vdivu_vv/profile.real_platform.yaml`
- `results/viota_m/profile.real_platform.yaml`
- `results/vmseq_vv/profile.real_platform.yaml`
- `results/vmul_vv/profile.real_platform.yaml`
- `results/vredsum_vs/profile.real_platform.yaml`
- `results/vrgather_vv/profile.real_platform.yaml`
- `results/vslideup_vx/profile.real_platform.yaml`
- `results/vsll_vv/profile.real_platform.yaml`

## Validation
- `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py` passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results` passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search.json --format json` passed and wrote `/tmp/profile-inst-latency-real-search.json`.
- `python3 -m json.tool /tmp/profile-inst-latency-real-search.json >/dev/null` passed.
- `python3 -m json.tool results/common/real_platform_inventory.json >/dev/null && python3 -m json.tool results/common/real_platform_field_status.json >/dev/null && python3 -m json.tool results/common/search_model_real_platform.json >/dev/null` passed.
- `find results/r01 results/r02 -name trace.json | wc -l` returned `6442`.
- `git diff --check` passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` failed closed as expected:
  - missing exact `Gate status: PASS`
  - missing machine-readable human approval file
  - 5 unresolved real-platform LLVM field-status conflicts

## Remaining Items
- The real-platform gate remains `NOT_READY`.
- Remaining blocking field-status rows: `vcpop_m` LMUL `m4` for `Latency`, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue`.
- The conflicting observed curve for `vcpop_m` LMUL `m4` includes T10/T11 deltas that do not fit one shared `startup + slope` tuple across all generated stream lengths. Follow-up should either add a targeted repeat/diagnostic experiment for this case or request explicit human approval for the remaining accepted risk set.
- Explicit human approval is still absent by design.

## BitLesson Delta
- Action: none
- Lesson ID(s): NONE
- Notes: `bitlesson-selector` returned `NONE` because the configured BitLesson knowledge base has no matching lesson entries for this candidate-simulator subtask.

## Goal Tracker Update Request

### Requested Changes:
- Mark the Round 2 shared candidate timing-model simulator implementation as completed with evidence from `scripts/search_model.py`, `results/common/search_model_real_platform.json`, and the validation commands above.
- Mark the stale real-platform search-summary equation issue as resolved; `results/common/search_model_real_platform_summary.md` now documents `startup + (N - 1) * ReleaseAtCycles` and `startup + (N - 1) * Latency`.
- Update the unresolved real-platform LLVM field-status open issue from 118 risks to 5 risks, all scoped to `vcpop_m` LMUL `m4`.
- Keep the real-platform gate and final completion tasks active because the gate is still `NOT_READY` and explicit human approval is absent.

### Justification:
The shared simulator required by the Round 1 review now exists and regenerates the real-platform artifacts through one candidate tuple path. The remaining blocker is narrower and explicit: one instruction/LMUL group has internally conflicting observations, and the gate correctly refuses to pass without either additional evidence or explicit human approval.
