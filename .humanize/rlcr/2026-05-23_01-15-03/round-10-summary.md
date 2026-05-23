# Round 10 Summary

## Work Completed

- Added Round 10 stronger-evidence lineage to Humanize2 capture without editing
  code, generated experiments, trace results, inventory, search artifacts,
  quality artifacts, profile sidecars, or goal-tracker/state files.
- Captured commit `f3bb455245cce28b1f61fd7447e1056e5c9903b2`: 108 generated
  T20 m4 resource-noreuse experiments plus global ProcResource evidence/search
  support.
- Captured commit `cd71b7ed3aa9d222306af23a51fe87efd76eddf9`: targeted
  `run_suite.py` selection filters for `--template-id`, `--id-regex`, and
  `--missing`.
- Captured commit `c1032a2c01949ecb9d651473dec1aa88695bb484`: 54 focused T12
  scalar-filler experiments and conservative T12/non-affine diagnostics.
- Captured commit `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`: incremental
  real gem5 refresh for the new 108 T20 and 54 T12 experiments with repeat 2,
  plus regenerated search/profile/inventory/quality/request artifacts.
- Updated current field-status capture from 111 inferred plus 39
  non-identifiable rows to 112 inferred plus 38 non-identifiable rows. The
  resolved row is `viota_m` `m4` `Latency`, inferred candidate `4`.
- Preserved request semantics: pending, not approved, not submitted, not a
  gate input, not an approval artifact, and not consumed by the gate.

## Files Changed

- `results/common/agentic_flow/h2_primitives.yaml`
- `results/common/agentic_flow/events.jsonl`
- `results/common/agentic_flow/replay.md`
- `results/common/agentic_flow/h2_manifest_notes.md`
- `results/common/agentic_flow/boards/execution_state.yaml`
- `results/common/agentic_flow/boards/experiment_matrix.yaml`
- `results/common/agentic_flow/boards/goal_tracker.yaml`
- `results/common/agentic_flow/boards/inference_state.yaml`
- `results/common/agentic_flow/boards/simulator_selection.yaml`
- `results/common/agentic_flow/views/status_panel.html`
- `results/common/agentic_flow/cartridges/rvv-profile-workflow.draft.html`
- `results/common/agentic_flow/artifacts/prompts/round-10-focused-evidence-capture-worker.md`
- `results/common/agentic_flow/artifacts/worker_contracts/worker-r10-capture.md`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-r10-capture.md`
- `results/common/agentic_flow/artifacts/verification/worker-r10-capture.md`
- `results/common/agentic_flow/artifacts/tool_calls/worker-r10-capture-normalized.json`
- `results/common/agentic_flow/artifacts/worker_outputs/coordinator-r10-focused-evidence.md`
- `results/common/agentic_flow/artifacts/verification/coordinator-r10-focused-evidence.md`
- `results/common/agentic_flow/artifacts/tool_calls/coordinator-r10-focused-evidence.json`
- `.humanize/rlcr/2026-05-23_01-15-03/round-10-summary.md`

## Validation

- BitLesson selector for runner/T12 tasks yielded `LESSON_IDS: NONE` because
  `.humanize/bitlesson.md` has no entries.
- Captured coordinator command:
  `python3 scripts/run_suite.py --all --generated-root experiments/generated --results-root results --template-id T20_PAIRWISE_PIPE_CLASSIFICATION --id-regex 'resource-noreuse$' --missing --repeat 2 --mode real_platform_profile --backend gem5_minor`.
- Captured coordinator command:
  `python3 scripts/run_suite.py --all --generated-root experiments/generated --results-root results --template-id T12_CONSUMER_RAW_GAP --id-regex 'fscalar-add$' --missing --repeat 2 --mode real_platform_profile --backend gem5_minor`.
- Captured coordinator command:
  `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json`.
- Captured coordinator command:
  `python3 scripts/analyze.py --all --root results --aggregate results/common/experiment_quality.md --mismatch-report results/common/mismatch_report.md --inventory results/common/real_platform_inventory.json`.
- Captured coordinator validation:
  `python3 -m unittest tests.test_run_suite_selection tests.test_gen_asm_t20_coverage tests.test_gen_asm_t12_focused tests.test_search_model_candidate_sim tests.test_check_calibration_gate_approval` passed, 33 tests OK.
- Captured coordinator validation:
  `python3 -m py_compile scripts/run_suite.py scripts/gen_asm.py scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/run_experiment.py` passed.
- Captured coordinator validation: `python3 -m pytest -q` passed, 33 tests.
- Captured coordinator validation: `git diff --check` and
  `git diff --cached --check` passed before commit `73b99c2e`.
- Synthetic gate passed.
- Real gate remains expected fail-closed: missing machine-readable human
  approval and unresolved real-platform LLVM field-status risks=38
  `status_counts={"non_identifiable": 38}`.
- Current hashes:
  - `inventory_sha256`: `728e0fd4570dc92e28f1683123bfde3e07d3903dbe026abc745766c0e06e0231`
  - `real_platform_field_status_sha256`: `9669b1f7ab8881d22d9a3072d0a9fe8fbe70654f8d1b6a3d75c9a37e184eed6b`
  - `search_model_real_platform_sha256`: `bf06a095edff3a56d03e3cb4223b590834783964ec7c19eaf2f876facdf9d623`
  - `experiment_quality_sha256`: `1a46e7ebfdbe692b3be557cad5c05bcbbc89812cf5c6f886f98a6b314f492fae`

## Remaining Items

- AC-16 remains incomplete. The real-platform gate must continue to fail closed
  until a machine-readable human approval artifact exists with current hash and
  risk-scope binding, or stronger evidence resolves all 38 non-identifiable
  rows.
- No `results/common/human_approval.*` artifact exists and this worker did not
  create one.
- The pending request must be presented to the human before any future
  `human_approval.json` is created.

## Goal Tracker Update Request

- Ask Codex to update Plan Version for Round 10.
- Mark T9 and T11 as progressed by Round 10 stronger T20/T12 evidence, but
  keep them `needs_changes` until the remaining real-platform issues are
  resolved or explicitly accepted.
- Add completed evidence rows for:
  - `f3bb455245cce28b1f61fd7447e1056e5c9903b2` - T20 m4 no-reuse ProcResource
    evidence.
  - `cd71b7ed3aa9d222306af23a51fe87efd76eddf9` - targeted `run_suite.py`
    selection filters.
  - `c1032a2c01949ecb9d651473dec1aa88695bb484` - focused T12 scalar-filler
    evidence path.
  - `73b99c2e1e95ed7828c5ce76d750a909bc83b5c5` - refreshed real-platform
    focused evidence and current request hashes.
- Update the open issue from 39 to 38 unresolved non-identifiable risks with
  the current hashes listed above.
- Record that no approval artifact exists, the request is not approved and not
  gate-consumed, and the real-platform gate remains fail-closed.

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: No BitLesson entries were selected; both Round 10 subtask selectors returned NONE because the knowledge base has no entries.
