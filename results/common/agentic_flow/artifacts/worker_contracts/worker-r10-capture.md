# Worker Contract: Round 10 Focused Evidence Capture

Round: 10
Worker: Round10FocusedEvidenceRefresh
Capture type: normalized reconstruction
Review driver: Round 10 stronger-evidence commits through
`73b99c2e1e95ed7828c5ce76d750a909bc83b5c5`
Status: focused evidence captured; not approval

## Objectives

- Record the T20 resource-noreuse, run-suite selection, T12 scalar-filler, and
  real-platform refresh commits as completed Round 10 evidence.
- Record the incremental real gem5 commands for the new 108 T20 and 54 T12
  generated experiments with `--repeat 2`.
- Capture regenerated search/profile/inventory/quality/request hashes without
  touching those artifacts.
- Update current Humanize2 state from 39 to 38 unresolved non-identifiable
  risks and from 111 to 112 inferred rows.
- Record `viota_m` `m4` `Latency` as the newly resolved inferred row.
- Preserve the approval boundary: no `results/common/human_approval.*` file,
  no approval semantics, and real gate remains fail-closed.
- Reference the coordinator-owned Round 10 RLCR summary without writing
  `.humanize/rlcr/**`.

## Owned Write Set

- `results/common/agentic_flow/**`
- `results/common/real_platform_risk_acceptance_request.json` only for
  non-semantic metadata wording if needed.

## Forbidden Write Set

- Code, tests, generated experiments, generated trace results, search
  artifacts, profile sidecars, inventory, field-status, quality, mismatch, or
  `.humanize/rlcr/**` control-plane files.
- Any human approval artifact under `results/common`.

## Required Validation

- YAML parse for `h2_primitives.yaml` and touched board YAML files.
- JSON parse for tool-call artifacts and the risk request JSON.
- JSONL parse for `events.jsonl`.
- Coordinator-owned summary section check for Work Completed, Files Changed,
  Validation, Remaining Items, Goal Tracker Update Request, and BitLesson
  Delta.
- Structural check that request hashes match live files, 38 risk IDs match the
  inventory order, no approval file exists, and the field-status summary has
  `blocking_total: 38`.
- `git diff --check` and `git diff --cached --check`.

The real-platform gate remains expected to fail closed. Passing it would imply
an approval boundary change outside this worker's scope.
