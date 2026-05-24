# Worker Contract: Round 15 Approval-Status Hardening

Worker: `Round15ApprovalStatusHardening`

Owned write scope:

- `scripts/approval_status.py`
- `scripts/check_calibration_gate.py`
- `scripts/analyze_core.py`
- `scripts/analyze_quality.py`
- `tests/test_check_calibration_gate_approval.py`
- `results/common/agentic_flow/**`

Read-only lineage scope:

- `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`
- `.humanize/rlcr/2026-05-23_01-15-03/round-10-review-result.md`

Forbidden write scope:

- `results/common/*approval*`
- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/search_model_real_platform.json`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `.humanize/rlcr/**`

Expected output:

- Analyzer discovery and gate validation share one top-level approval-status
  decision helper.
- The `human_approved: true` vocabulary parity regression passes.
- The current pending request remains not approved, not a gate input, and not
  gate-consumed.
- AC-16 remains fail-closed until explicit human approval exists or stronger
  evidence resolves the 9 unresolved rows.
