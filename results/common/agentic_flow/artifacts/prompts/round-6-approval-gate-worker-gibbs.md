# Prompt Capture: Round 6 Approval-Gate Worker Gibbs

Prompt ID: round-6-approval-gate-worker-gibbs
Task owner: RLCR coordinator
Worker: Gibbs
Round: 6
Capture type: normalized reconstruction

This prompt capture is not a verbatim chat transcript. It is reconstructed
from the Round 6 summary, Round 6 review result, and commit
`ea7c0acaa5d144ffd8aa5bb0ac3f8f17b8b156ac`.

## Requested Scope

- Harden the real-platform approval gate so `non_identifiable` LLVM-facing
  field-status rows remain unresolved approval-bound risks.
- Require any future machine-readable approval to bind both current
  `inventory_sha256` and current `real_platform_field_status_sha256`.
- Require approval to include explicit accepted risk IDs or an all-risk
  acceptance for unresolved real-platform field-status risks.
- Add focused approval-gate regression tests for missing hashes, stale hashes,
  missing risk scope, and valid all-risk acceptance.
- Regenerate the inventory and quality artifacts that reflect the hardened
  approval boundary.
- Preserve the approval boundary: do not create or imply a
  `results/common/*approval*` artifact, and do not mark AC-16 complete.

## Write Boundaries

Allowed write set reconstructed from the committed diff:

- `scripts/analyze.py`
- `scripts/check_calibration_gate.py`
- `tests/test_check_calibration_gate_approval.py`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`

Forbidden write set for the approval-gate worker:

- `.humanize/**`
- `results/common/*approval*`
- unrelated script, test, result, or capture paths outside the assigned
  approval-gate hardening and regenerated-artifact scope.

## Required Inputs

- `docs/plan.md`
- `.humanize/rlcr/2026-05-23_01-15-03/round-6-summary.md`
- Existing real-platform field-status data in
  `results/common/real_platform_field_status.json`
- Existing approval-gate implementation in `scripts/check_calibration_gate.py`
- Existing analysis inventory writer in `scripts/analyze.py`

## Expected Artifacts

- Code/test commit:
  `ea7c0acaa5d144ffd8aa5bb0ac3f8f17b8b156ac`
- Regenerated real-platform artifacts:
  - `results/common/real_platform_inventory.json`
  - `results/common/experiment_quality.md`
- Verification evidence summarized in
  `results/common/agentic_flow/artifacts/verification/worker-r6-gibbs-approval-gate.md`
- Normalized tool-call capture in
  `results/common/agentic_flow/artifacts/tool_calls/worker-r6-gibbs-approval-gate-normalized.json`

## Model and Runtime Assumptions

The exact model, reasoning effort, and timeout for Worker Gibbs were not
recorded in checked-in artifacts. Replay should treat this package as a
normalized Humanize2 capture of the work product, not as a transcript-level
reproduction of the original dispatch.

## Success Criteria

- `non_identifiable` field-status rows are blocking unresolved risks for the
  real-platform gate unless valid approval covers them.
- Human approval without current `inventory_sha256` fails.
- Human approval without current `real_platform_field_status_sha256` fails.
- Stale inventory or field-status hashes fail.
- Stale inventory-side acceptance alone cannot satisfy unresolved field-status
  risk acceptance.
- Explicit all-risk acceptance can satisfy the unresolved field-status risk
  scope when the approval is otherwise valid.
- Synthetic calibration still passes.
- Real-platform profiling fails closed on missing `Gate status: PASS`, missing
  approval, and the 39 unresolved `non_identifiable` rows.
- No `results/common/*approval*` artifact is created.

BitLesson selector result for this task: `LESSON_IDS: NONE`.
