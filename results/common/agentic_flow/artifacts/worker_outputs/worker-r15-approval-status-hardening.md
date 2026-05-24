# Worker Output: Round 15 Approval-Status Hardening

Implemented a shared approval-status decision path for the current-head
approval review findings.

Changes:

- Added `scripts/approval_status.py` with a shared top-level approval decision
  helper.
- Updated `scripts/check_calibration_gate.py` to use that helper for
  `human_approval_failures()`.
- Updated `scripts/analyze_quality.py` to use the same helper for
  `discover_approval()`.
- Kept nested accepted-risk extraction recursive.
- Added a regression for a top-level `human_approved: true` artifact proving
  analyzer discovery and gate validation agree.

Captured boundary:

- Prior hardening commit: `9a85412b`.
- Follow-up vocabulary-parity commit: `f1687ac9`.

Approval boundary:

- No approval artifact was created.
- The request remains pending, not approved, not a gate input, and not
  gate-consumed.
- The real-platform gate still fails closed because `Gate status: PASS`, a
  machine-readable approval artifact, and accepted scope for the 9 unresolved
  risks are absent.
