# Humanize2 Manifest Notes

Status: Round 7 request-worker package after the Round 6 approval-gate worker
capture, the Round 5 candidate-simulator worker capture, and Round 6 review
commit `fdcc1137`.

This tree mirrors the Humanize2 concepts in `docs/plan.md` without depending on
an available Humanize2 hub. It records enough structure for an empty-context
session to replay the RLCR workflow with plain scripts, then map the same
control flow into executable Humanize2 primitives.

Current mode labels:

- `synthetic_calibration`: allowed to use configured cmodel ground truth for
  mismatch repair.
- `real_platform_profile`: must stop on coverage, stability, confidence,
  documented assumptions, conflict resolution, and human approval.

Current gate state:

- Synthetic calibration: pass, see `results/common/mismatch_report.md`.
- Real gem5 checked-in r01/r02 traces: 7190, with 178/178 required groups and
  3595 stable repeat groups.
- Real-platform field status: 150 rows, 111 inferred, 39 non-identifiable, 0
  conflict, 0 insufficient-evidence.
- Real-platform gate: `NOT_READY`, see `results/common/experiment_quality.md`.
  The approval artifact is absent and must not be created without explicit
  user approval tied to current risk IDs and hashes.
- Risk request: `results/common/real_platform_risk_acceptance_request.json`
  exists as a pending, not-approved request for human decision. It is not
  consumed by the gate and is not an approval artifact.
- Current Round 6 hashes are `4f25f066...` for inventory, `904cca46...` for
  field status, `d31ef890...` for real search, and `b6b6b1dd...` for
  experiment quality. Future approval must bind at least the current inventory
  and field-status hashes and must accept the current unresolved risk scope.
  Older Round 4 and Round 5 hashes remain only in explicitly historical
  capture artifacts and events.

Round 5 ownership:

- This worker owns only `results/common/agentic_flow/**`.
- Worker Anscombe owned `scripts/search_model.py`,
  `tests/test_search_model_candidate_sim.py`, generated real-platform outputs,
  common real-platform JSON/Markdown artifacts, and
  `results/*/profile.real_platform.yaml`; current `main` commit `773f27d6`
  is that worker's code/result change.
- Round 5 review accepted the candidate-simulator scope for peer-side T20 and
  short T12 exactness, but requested this missing code-worker capture package
  plus separate AC-16 approval-bound risk handling.
- `.humanize/rlcr/**` is read-only for this worker; replay points there for
  prompt/result history.

Round 6 ownership:

- Worker Gibbs owned `scripts/analyze.py`, `scripts/check_calibration_gate.py`,
  `tests/test_check_calibration_gate_approval.py`,
  `results/common/real_platform_inventory.json`, and
  `results/common/experiment_quality.md`; commit `ea7c0aca` is that worker's
  approval-gate hardening change.
- Round 6 review accepted the approval-gate behavior: `non_identifiable` rows
  are unresolved approval-bound risks, approval must bind current inventory and
  field-status hashes, and approval must include accepted risk scope.
- Round 7 now includes the Gibbs capture refresh plus the
  `Round7RiskRequest` worker. The request-worker owns only
  `results/common/real_platform_risk_acceptance_request.json` and
  `results/common/agentic_flow/**`. It does not create approval and does not
  mark AC-16 complete.
- Empty-context replay must present the pending request to the human before any
  future `human_approval.json` is created. The human choices are: accept all
  current risks with a future gate-consumed artifact, reject and require
  stronger experiments/modeling, or accept selected listed risk IDs.
