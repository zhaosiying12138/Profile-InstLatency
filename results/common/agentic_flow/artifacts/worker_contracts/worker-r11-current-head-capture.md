# Worker Contract: Round 11 Current-Head Capture

Worker: `Round11CurrentHeadCapture`

Owned write scope:

- `results/common/agentic_flow/**`

Forbidden write scope:

- `results/common/*approval*`
- `results/common/real_platform_risk_acceptance_request.json`
- `results/common/search_model_real_platform.json`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `.humanize/rlcr/**`

Expected output:

- Current 9-risk boundary recorded in boards, replay, status view, cartridge, events, and manifest.
- Search reproducibility fix recorded without changing the request-bound search hash.
- Approval boundary preserved as pending/not-approved/not-gate-consumed.
