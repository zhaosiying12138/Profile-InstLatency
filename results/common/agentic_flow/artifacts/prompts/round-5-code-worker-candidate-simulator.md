# Prompt Capture: Round 5 Candidate-Simulator Code Worker

Prompt ID: round-5-code-worker-candidate-simulator
Task owner: RLCR coordinator
Worker: Anscombe
Round: 5
Capture type: normalized reconstruction

This prompt capture is not a verbatim chat transcript. The original worker
prompt was not checked in. It is reconstructed from the Round 5 prompt,
Round 5 summary, Round 5 review result, and commit
`773f27d67e8306ec8fbafc434dcd158953e71e95`.

## Requested Scope

- Fix the Round 4 candidate-simulator gaps for peer-side T20 constraints and
  short T12 exactness.
- Add focused regression coverage for those two behaviors.
- Regenerate real-platform search, field-status, inventory, quality, summary,
  and affected profile sidecar artifacts.
- Preserve the real-platform approval boundary: no approval artifact may be
  created and AC-16 must remain fail-closed without explicit human approval.

## Write Boundaries

Allowed write set reconstructed from the committed diff:

- `scripts/search_model.py`
- `tests/test_search_model_candidate_sim.py`
- `results/common/search_model_real_platform.json`
- `results/common/search_model_real_platform_summary.md`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/vredsum_vs/profile.real_platform.yaml`

Forbidden write set for the code worker:

- `.humanize/**`
- `results/common/*approval*`
- unrelated scripts, tests, generated traces, and agentic-flow capture files
  unless separately assigned to a capture worker.

## Required Inputs

- `docs/plan.md`
- `.humanize/rlcr/2026-05-23_01-15-03/round-5-prompt.md`
- `.humanize/rlcr/2026-05-23_01-15-03/round-4-review-result.md`
- Existing checked-in real-platform traces under `results/r01` and
  `results/r02`
- Existing candidate-simulator tests in `tests/test_search_model_candidate_sim.py`

## Expected Artifacts

- Code/test commit:
  `773f27d67e8306ec8fbafc434dcd158953e71e95`
- Regenerated real-platform artifacts:
  - `results/common/search_model_real_platform.json`
  - `results/common/search_model_real_platform_summary.md`
  - `results/common/real_platform_field_status.json`
  - `results/common/real_platform_inventory.json`
  - `results/common/experiment_quality.md`
  - `results/vredsum_vs/profile.real_platform.yaml`
- Verification evidence summarized in
  `results/common/agentic_flow/artifacts/verification/worker-r5-code.md`
- Normalized tool-call capture in
  `results/common/agentic_flow/artifacts/tool_calls/worker-r5-code-normalized.json`

## Model and Runtime Assumptions

The exact model, reasoning effort, and timeout for Worker Anscombe were not
recorded in checked-in artifacts. Replay should treat this package as a
normalized Humanize2 capture of the work product, not as a transcript-level
reproduction of the original dispatch.

## Success Criteria

- T20 pair observations are mirrored into existing peer rows, so peer-only
  participants are constrained by traces where they appear as
  `pair_instruction_id`.
- `vredsum_vs` has non-empty peer-side T20 evidence in real-platform search
  output.
- T12 clean-prefix exact latency requires trailing no-stall residual plateau
  coverage before rendering `exact_fit`.
- A K0/K1 short sweep remains `non_identifiable` rather than overclaiming an
  exact latency.
- Focused unit tests cover peer-side T20 mirroring and the T12 short-sweep
  guard.
- Real-platform artifacts are regenerated from checked-in traces and preserve
  the current hash snapshot.
- Synthetic calibration still passes.
- Real-platform profiling remains fail-closed because `Gate status: PASS` and a
  machine-readable approval artifact are absent.
- No `results/common/*approval*` artifact is created.

BitLesson selector result for this task: `LESSON_IDS: NONE`.
