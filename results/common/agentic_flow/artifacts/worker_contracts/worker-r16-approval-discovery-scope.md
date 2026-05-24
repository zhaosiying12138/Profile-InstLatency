# Worker Contract: Round 16 Approval Discovery Scope

Worker: `Round16ApprovalDiscoveryScope`

Objective: integrate and capture the approval-discovery scope repair at commit
`366be5b8`.

Owned write set:

- `scripts/approval_status.py`
- `scripts/check_calibration_gate.py`
- `scripts/analyze_quality.py`
- `tests/test_check_calibration_gate_approval.py`
- `results/common/agentic_flow/**`

Forbidden write set:

- `results/common/*approval*`
- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/search_model_real_platform.json`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `.humanize/rlcr/**`

Control-plane notes:

- `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md` and
  `.humanize/rlcr/2026-05-23_01-15-03/round-10-review-result.md` are
  Codex-reviewer-owned state. They are captured as lineage references, not
  worker-owned files.
- The real-platform approval request remains pending and is not gate-consumed.
