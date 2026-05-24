# Worker Output: Round 16 Approval Discovery Scope

Implemented and committed the approval-discovery scope repair at
`366be5b8`.

Changes:

- Added `human_approval_file()` to `scripts/approval_status.py`.
- Made `scripts/check_calibration_gate.py` delegate approval-file lookup to the
  shared helper.
- Made `scripts/analyze_quality.py` discover only the same
  gate-discoverable common approval file.
- Added
  `test_nested_human_approval_is_not_discovered_or_gate_consumed` to prove
  nested `results/r01/**/human_approval.json` files are ignored by both paths.

Current AC-16 state is unchanged: no approval artifact exists under
`results/common`, the pending request remains not approved, and the real gate
fails closed on missing `Gate status: PASS`, missing machine-readable
approval, and 9 unresolved `non_identifiable` risks.
