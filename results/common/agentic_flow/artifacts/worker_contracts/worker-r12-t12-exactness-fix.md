# Worker Contract: Round 12 T12 Exactness Fix

Worker: `Round12T12ExactnessFix`

Owned write scope:

- `scripts/search_model_impl.py`
- `tests/test_search_model_candidate_sim.py`
- `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`
- `.humanize/rlcr/2026-05-23_01-15-03/round-10-review-result.md`
- `results/common/agentic_flow/**`

Forbidden write scope:

- `results/common/*approval*`
- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/search_model_real_platform.json`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `.humanize/rlcr/2026-05-23_01-15-03/state.md`

Expected output:

- `91201d20` fixes matched-control exactness.
- AC-9 is restored.
- AC-16 remains fail-closed pending explicit human approval or stronger evidence for the 9 unresolved rows.
