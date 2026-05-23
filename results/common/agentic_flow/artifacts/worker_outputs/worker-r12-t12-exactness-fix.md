# Worker Output: Round 12 T12 Exactness Fix

Implemented commit `91201d20`.

Changes:

- `t12_matched_control_constraint()` now computes exact latency from all positive-stall equations `gap * cadence + stall`.
- Exact latency is claimed only when all positive stalls agree and all zero-stall convergence gaps are consistent.
- Disagreeing positive-stall evidence remains `non_identifiable`.

Evidence:

- Cadence-2 stalls `[3, 1, 0, 0]` now infer `Latency = 3`.
- A cadence-2 disagreement case now fails closed.
- Current real-platform search output remains byte-for-byte identical to `results/common/search_model_real_platform.json`, so checked-in real artifacts did not need regeneration.

Approval boundary:

- No approval artifact was created.
- The request remains pending and not gate-consumed.
