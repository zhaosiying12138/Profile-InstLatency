# Round 10 Summary

## Work Completed

- Recorded explicit human approval for the 9 current real-platform
  `non_identifiable` LLVM-facing risks in `results/common/human_approval.json`.
- Bound the approval to the current inventory, field-status, search, quality,
  and risk-request hashes plus the exact accepted risk IDs.
- Updated `results/common/real_platform_risk_acceptance_request.json` to
  `fulfilled_by_human_approval` while preserving that the request itself is not
  a gate input and not an approval artifact.
- Regenerated real-platform analyzer artifacts so
  `results/common/experiment_quality.md` reports `Gate status: PASS` and
  `results/common/real_platform_inventory.json` reports
  `confidence.level: approved_real_platform`.
- Captured the Round 17 human-approval transition in Humanize2 artifacts:
  prompt, decision, coordinator output, verification, tool-call JSON, boards,
  replay, events, cartridge, status panel, and manifest notes.
- Kept the accepted rows as known approval-bound risks. This round does not
  infer exact hardware values for those 9 rows.

## Accepted Risk IDs

- `llvm_field_status:vcpop_m:m1:Latency:non_identifiable`
- `llvm_field_status:vcpop_m:m2:Latency:non_identifiable`
- `llvm_field_status:vcpop_m:m4:Latency:non_identifiable`
- `llvm_field_status:vcpop_m:m4:ReleaseAtCycles:non_identifiable`
- `llvm_field_status:vcpop_m:m4:ProcResource:non_identifiable`
- `llvm_field_status:vcpop_m:m4:NumMicroOps:non_identifiable`
- `llvm_field_status:vcpop_m:m4:SingleIssue:non_identifiable`
- `llvm_field_status:vrgather_vv:m4:Latency:non_identifiable`
- `llvm_field_status:vslideup_vx:m4:Latency:non_identifiable`

## Files Changed

- `results/common/human_approval.json`
- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/common/agentic_flow/h2_primitives.yaml`
- `results/common/agentic_flow/events.jsonl`
- `results/common/agentic_flow/replay.md`
- `results/common/agentic_flow/h2_manifest_notes.md`
- `results/common/agentic_flow/boards/execution_state.yaml`
- `results/common/agentic_flow/boards/goal_tracker.yaml`
- `results/common/agentic_flow/boards/inference_state.yaml`
- `results/common/agentic_flow/boards/simulator_selection.yaml`
- `results/common/agentic_flow/views/status_panel.html`
- `results/common/agentic_flow/cartridges/rvv-profile-workflow.draft.html`
- `results/common/agentic_flow/artifacts/prompts/round-17-human-approval-coordinator.md`
- `results/common/agentic_flow/artifacts/decisions/round-17-human-approval.md`
- `results/common/agentic_flow/artifacts/worker_outputs/coordinator-r17-human-approval.md`
- `results/common/agentic_flow/artifacts/verification/coordinator-r17-human-approval.md`
- `results/common/agentic_flow/artifacts/tool_calls/coordinator-r17-human-approval.json`
- `.humanize/rlcr/2026-05-23_01-15-03/round-10-summary.md`

## Validation

- BitLesson selector was invoked for this approval/gate continuation and
  returned `LESSON_IDS: NONE`.
- YAML/JSON/JSONL/HTML parse checks passed for Humanize2 boards,
  `h2_primitives.yaml`, tool-call JSON, approval/request/inventory/search
  artifacts, `events.jsonl`, and the draft cartridge; event count is 80.
- Approval scope validation passed: accepted risk IDs in
  `human_approval.json`, `real_platform_inventory.json` unresolved rows, and
  `real_platform_risk_acceptance_request.json` match exactly, count 9.
- `python3 -m unittest tests.test_check_calibration_gate_approval` passed, 11
  tests.
- `python3 -m py_compile scripts/approval_status.py scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/search_model_impl.py scripts/search_model_support.py scripts/check_calibration_gate.py scripts/analyze.py scripts/analyze_core.py scripts/analyze_quality.py scripts/run_experiment.py` passed.
- `python3 -m pytest -q` passed, 63 tests.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results` passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-r17-search.json --format json` passed, and `cmp /tmp/profile-inst-latency-r17-search.json results/common/search_model_real_platform.json` passed.
- `git diff --check` and `git diff --cached --check` passed before commit.

Current hashes:

- `human_approval_sha256`: `f85dc41ffdea94249da33fe9dad29b6879de51616463b806cf4c6cd27228f2fd`
- `inventory_sha256`: `857590b16d9690eaa502f2fb589b8b0e79a20f5b6dba2112c44e02d01c379759`
- `real_platform_field_status_sha256`: `079cb94d27e98bdcf9df0ae0595a6e12b101e4c8c5a3d46f7d627dd4c81c1432`
- `search_model_real_platform_sha256`: `3d72fd2e87b517e3e7ba3699eb214b8f35874055f3ed51c519aa4671d5f002bd`
- `experiment_quality_sha256`: `57c8d84dff3816459fffbbdab3643e3c196bb6adc17b4db2dcc5accada9905ce`
- `risk_acceptance_request_sha256`: `1605e9af6e64d5a8c77b466c7cd8ddf7ad68fe6fe161821e4fb5054418daa913`

## Remaining Items

- No stronger-evidence work remains required for the 9 listed risks because the
  human owner explicitly accepted them for the current artifact hashes.
- The 9 accepted rows remain `non_identifiable` and must not be treated as
  exact inferred hardware parameters.

## Goal Tracker Update Request

### Requested Changes

- Update Plan Version for Round 17 human approval and real-platform gate pass.
- Add a Plan Evolution Log entry recording that explicit current-hash-bound
  human approval was supplied for the exact 9 current `non_identifiable` risk
  IDs, `results/common/human_approval.json` was created, analyzer artifacts
  were regenerated, and the real-platform gate passed.
- Mark T9 as completed/verified for the real gem5 timing suite and
  approval-ready quality report: coverage, repeatability, marker contract,
  zero conflict rows, explicit approval, and real gate all pass.
- Mark T11 as completed/verified for real-platform gate enforcement: the gate
  now passes only with the machine-readable approval artifact and accepted risk
  scope.
- Update T6/T12 notes to include the Round 17 Humanize2 capture package and
  event count 80.
- Resolve the Open Issue for the 9 non-identifiable real-platform
  LLVM-facing rows by noting they were explicitly accepted through
  `results/common/human_approval.json` with the current hashes listed above.
- Mark AC-16 as met for the current real-platform profiling artifact set.

### Justification

The original AC-16 blocker was absent explicit human approval for the 9
approval-bound real-platform rows. The human owner approved those exact risks,
the approval is machine-readable and hash-bound, analyzer artifacts record the
approved state, and `check_calibration_gate.py --mode real_platform_profile`
now passes. This satisfies the planned stop condition without converting known
risks into fabricated exact values.

## BitLesson Delta

none
