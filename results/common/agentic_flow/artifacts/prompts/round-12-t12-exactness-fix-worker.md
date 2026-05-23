# Round 12 T12 Exactness Fix Worker Prompt

Fix the matched-control T12 exact-latency overclaim found by review.

Requirements:

- For matched dependent/control T12 observations, infer exact latency from the positive-stall equations `gap * cadence + stall`.
- Require every positive stall to produce the same latency value.
- Require the zero-stall convergence plateau to be consistent with that latency.
- If the equations disagree, fail closed as `non_identifiable`.
- Preserve the current real-platform request as pending and not approved.

Verification:

- Add cadence-2 partial-stall and disagreement regression tests.
- Run full pytest, py_compile, synthetic gate, real-platform fail-closed gate, and real search byte-reproduction.
