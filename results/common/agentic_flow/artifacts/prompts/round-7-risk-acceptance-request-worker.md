# Prompt Capture: Round 7 Risk-Acceptance Request Worker

Prompt ID: round-7-risk-acceptance-request-worker
Task owner: RLCR coordinator
Worker: Round7RiskRequest
Round: 7
Capture type: normalized self-capture

This prompt capture records the request-worker task that followed commit
`e175258a`. The task is to create a machine-readable risk-acceptance request
artifact, not a human approval artifact, and to update the Humanize2 capture so
an empty-context replay knows to present the request to the human before any
future `human_approval.json` is created.

## Requested Scope

- Create `results/common/real_platform_risk_acceptance_request.json`.
- Keep the request status pending and not approved.
- Include the current Round 6 inventory and field-status hashes.
- Include all 39 unresolved risk IDs from
  `results/common/real_platform_inventory.json` `field_status.unresolved`.
- Include the exact real-platform gate command:
  `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`.
- Record the expected current fail-closed reasons:
  missing `Gate status: PASS`, missing machine-readable human approval, and
  39 unresolved `non_identifiable` risks.
- Present the human decision choices: accept all current risks with a future
  `human_approval.json`, reject and require stronger experiments/modeling, or
  accept selected listed risk IDs.
- Make clear the request is not consumed by the gate and is not an approval
  artifact.

## Write Boundaries

Allowed write set:

- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/agentic_flow/**`

Forbidden write set:

- `.humanize/**`
- scripts
- tests
- generated real-platform search, inventory, field-status, or quality outputs
  other than the new request artifact
- any new file under `results/common` whose name contains `approval`

## Required Inputs

- `results/common/real_platform_inventory.json`
- `results/common/real_platform_field_status.json`
- `results/common/search_model_real_platform.json`
- `results/common/experiment_quality.md`
- Existing Round 5 and Round 6 Humanize2 capture files under
  `results/common/agentic_flow/**`

## Expected Artifacts

- Request:
  `results/common/real_platform_risk_acceptance_request.json`
- Prompt:
  `results/common/agentic_flow/artifacts/prompts/round-7-risk-acceptance-request-worker.md`
- Contract:
  `results/common/agentic_flow/artifacts/worker_contracts/worker-r7-risk-request.md`
- Output:
  `results/common/agentic_flow/artifacts/worker_outputs/worker-r7-risk-request.md`
- Verification:
  `results/common/agentic_flow/artifacts/verification/worker-r7-risk-request.md`
- Tool calls:
  `results/common/agentic_flow/artifacts/tool_calls/worker-r7-risk-request.json`

## Success Criteria

- The request JSON parses and contains exactly 39 risk IDs.
- No status field marks the request approved or truthy.
- No new approval-named file appears under `results/common`.
- The real-platform gate still fails closed on the same expected reasons.
- `h2_primitives.yaml`, all board YAML, all tool-call JSON, the request JSON,
  and `events.jsonl` parse.
- Registered Humanize2 paths exist.
- Replay, boards, status panel, cartridge, and manifest notes all direct an
  empty-context run to present the request to the human before any future
  `human_approval.json` is created.

BitLesson selector result for this task: `LESSON_IDS: NONE`.
