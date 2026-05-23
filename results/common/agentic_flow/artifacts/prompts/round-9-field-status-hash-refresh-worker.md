# Prompt Capture: Round 9 Field-Status Hash Refresh Worker

Prompt ID: round-9-field-status-hash-refresh-worker
Task owner: RLCR coordinator
Worker: Round9FieldStatusHashRefresh
Round: 9
Capture type: normalized reconstruction

This prompt capture records the Humanize2 capture update that follows Round 9
code-worker commit `f6614b00177e4139c8cfcf53b349b69478942b66`. That commit
fixed `scripts/search_model.py` so `non_identifiable` field-status rows are
counted as blocking, added a regression test, and regenerated real-platform
artifacts. The capture task refreshes request semantics and agentic-flow state
only; it does not create approval and does not submit anything to the gate.

## Requested Scope

- Update `results/common/real_platform_risk_acceptance_request.json` to Round
  9 request semantics:
  - `round: 9`
  - `request_worker: Round9FieldStatusHashRefresh`
  - pending, not approved, not submitted, not gate consumed
  - `approved`, `is_gate_input`, `is_approval_artifact`, and `gate_consumed`
    all `false`
- Preserve the exact unresolved risk ID order from
  `results/common/real_platform_inventory.json` `field_status.unresolved`.
- Preserve current hash binding:
  - inventory:
    `671f5ca4a295aca29a62ee6027b4f6cd756cc49572f0558a98ee8dbf786fbe37`
  - field status:
    `0146ac9ce41185d776f70a8573f8792f7e14a4d58d3f29d36ac7faa1f9f82195`
  - real-platform search:
    `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73`
  - experiment quality:
    `b63c3bfa1d9c943660a21b3427bc3b9f3402ee6fe6fc5d7a8af5014e197ebb1e`
- Record Round 8 review blockers: AC-16 remains blocked, and the
  pre-Round-9 field-status sidecar undercounted `non_identifiable` blockers.
- Record Round 9 code-worker outcome: field-status `blocking_total` is now 39
  and `blocking_status_counts.non_identifiable` is 39.
- Refresh Humanize2 primitives, boards, replay notes, manifest notes, status
  panel, cartridge draft, events, worker output, verification, and tool-call
  capture.
- Keep AC-16 blocked until explicit current-hash-bound human approval exists
  or stronger evidence resolves all 39 approval-bound risks.

## Write Boundaries

Allowed write set:

- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/agentic_flow/**`

Forbidden write set:

- `.humanize/**`
- scripts
- tests
- generated real-platform sidecars other than the already-refreshed request
  metadata
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/common/search_model_real_platform.json`
- any new approval artifact under `results/common`

## Required Inputs

- Round 9 code worker commit
  `f6614b00177e4139c8cfcf53b349b69478942b66`
- `results/common/real_platform_inventory.json`
- `results/common/real_platform_field_status.json`
- `results/common/search_model_real_platform.json`
- `results/common/experiment_quality.md`
- `results/common/real_platform_risk_acceptance_request.json`
- Existing Humanize2 capture files under `results/common/agentic_flow/**`

## Expected Artifacts

- Prompt:
  `results/common/agentic_flow/artifacts/prompts/round-9-field-status-hash-refresh-worker.md`
- Contract:
  `results/common/agentic_flow/artifacts/worker_contracts/worker-r9-field-status-hash-refresh.md`
- Output:
  `results/common/agentic_flow/artifacts/worker_outputs/worker-r9-field-status-hash-refresh.md`
- Verification:
  `results/common/agentic_flow/artifacts/verification/worker-r9-field-status-hash-refresh.md`
- Tool calls:
  `results/common/agentic_flow/artifacts/tool_calls/worker-r9-field-status-hash-refresh-normalized.json`

## Success Criteria

- The request JSON parses and has Round 9 metadata with pending/not approved
  status.
- Request `risk_ids` and `risk_scope.risk_ids` match the inventory
  `field_status.unresolved` risk ID order exactly.
- Request hashes match the live SHA-256 values for inventory, field status,
  real-platform search, and experiment quality.
- `results/common/real_platform_field_status.json` reports
  `blocking_total: 39` and
  `blocking_status_counts.non_identifiable: 39`.
- No approval artifact exists under `results/common`.
- The synthetic gate passes.
- The real-platform gate still fails closed on missing `Gate status: PASS`,
  missing machine-readable approval, and 39 unresolved `non_identifiable`
  risks.
- JSON, YAML, JSONL, tool-call JSON, structural checks, unit tests, and
  `git diff --check` pass.

BitLesson selector result for this task: `LESSON_IDS: NONE`.
