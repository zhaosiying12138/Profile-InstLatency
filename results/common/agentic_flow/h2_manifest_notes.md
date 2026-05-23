# Humanize2 Manifest Notes

Status: Round 13 control-plane ownership repair after commit
`91201d20`.

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
- Real-platform traces: 7660, with 178/178 required groups and 3815 stable
  repeat groups.
- Real-platform field status: 150 rows, 141 inferred, 9 non-identifiable, 0
  conflict, 0 insufficient-evidence.
- Real-platform gate: `NOT_READY`, see `results/common/experiment_quality.md`.
  The approval artifact is absent and must not be created without explicit
  user approval tied to current risk IDs and hashes.
- Field-status blocking summary: `blocking_total: 9` and
  `blocking_status_counts.non_identifiable: 9`.
- Risk request: `results/common/real_platform_risk_acceptance_request.json`
  exists as a Round 11 pending, not-approved request for human decision. It is
  not consumed by the gate and is not an approval artifact.
- Current Round 11 hashes are `197787ab...` for inventory, `079cb94d...` for
  field status, `2f3b78eb...` for real search, and `d3c2e41...` for
  experiment quality. Future approval must bind at least the current inventory
  and field-status hashes and must accept the current unresolved risk scope.
  Older Round 4 through Round 7 hashes remain only in explicitly historical
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
- Round 7 includes the Gibbs capture refresh plus the `Round7RiskRequest`
  worker. The request-worker owned only
  `results/common/real_platform_risk_acceptance_request.json` and
  `results/common/agentic_flow/**`. It did not create approval and did not
  mark AC-16 complete.
- Round 8 review kept AC-16 blocked and identified a field-status sidecar
  summary bug: `non_identifiable` rows were approval-bound but not counted in
  `blocking_total`.
- Round 9 code-worker commit `f6614b00` fixed that sidecar inconsistency,
  regenerated current hashes, and left the approval boundary intact. This
  capture worker refreshes only the request metadata and Humanize2 state.
- Round 10 commits `f3bb4552`, `cd71b7ed`, `c1032a2c`, and `73b99c2e`
  added stronger T20 m4 no-reuse ProcResource evidence, targeted incremental
  suite selection, focused T12 scalar-filler evidence, and refreshed checked-in
  real-platform artifacts. At that boundary the field status was 112 inferred and 38
  non-identifiable; `viota_m` `m4` `Latency` is the newly resolved inferred
  row. The request remains pending, not approved, not a gate input, and not
  gate-consumed.
- Post-Round-10 commits `77d181af`, `6ff16b7c`, and `88c9e6e5`
  canonicalized pure ProcResource mirror assignments, added matched T12
  control experiments, and added focused `vcpop_m` `m4` R11 diagnostics.
  Current artifacts report 141 inferred rows and 9 non-identifiable rows.
  Commit `8ec7a8a8` fixed the documented `/tmp` search reproduction path while
  preserving the request-bound search hash.
- Round 12 commit `91201d20` fixed the matched-control T12 exactness rule:
  exact latency is inferred from agreeing positive-stall equations
  `gap * cadence + stall`, zero-stall convergence must be consistent, and
  disagreement fails closed. The cadence-2 partial-stall regression now infers
  `Latency = 3`; real-platform search remains byte-reproducible against the
  checked-in artifact, so request-bound hashes are unchanged.
- Round 13 repairs replay ownership: worker write scopes no longer include
  `.humanize/rlcr/**`. The Round 10 summary is coordinator-owned, while
  `goal-tracker.md` and `round-10-review-result.md` are Codex-reviewer-owned
  control-plane files. `.humanize/rlcr/**` may still appear as read-only
  lineage evidence.
- Empty-context replay must present the pending request to the human before any
  future `human_approval.json` is created. The human choices are: accept all
  current risks with a future gate-consumed artifact, reject and require
  stronger experiments/modeling, or accept selected listed risk IDs.
