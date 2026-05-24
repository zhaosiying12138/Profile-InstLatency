# Decision: Round 15 Approval-Status Hardening

Round 10 re-review found two approval-status issues at the current-head
boundary:

- Commit `9a85412b` fixed the contradictory artifact case where top-level
  `status: pending` could be overridden by nested
  `risk_acceptance.status: approved`.
- A follow-up review found that analyzer approval discovery and gate approval
  validation disagreed on the top-level `human_approved` spelling.

The selected repair is a shared top-level approval decision helper in
`scripts/approval_status.py`. Both `scripts/check_calibration_gate.py` and
`scripts/analyze_quality.py` use this helper for artifact-level approval
status. Accepted risk IDs remain recursively discoverable so nested
`risk_acceptance.accepted_risk_ids` can still define the accepted-risk scope.

The canonical top-level approval vocabulary is:

- `approved`
- `human_approved`
- `human_approval`
- `status`
- `human_approval_status`
- `approval_status`

Every present top-level approval/status field must be approved/granted/pass.
Nested `status` values are not artifact approval decisions.

No `results/common/*approval*` artifact was created. The real-platform gate
continues to fail closed on missing `Gate status: PASS`, missing
machine-readable approval, and the 9 unresolved `non_identifiable` rows.
