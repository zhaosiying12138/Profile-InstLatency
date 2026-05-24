# Decision: Round 14 Formula-Fit Coverage Guard

The real-platform formula-fit summary must not claim a complete exact formula
unless every required LMUL row for that instruction field is exact.

Required LMUL set:

- `m1`
- `m2`
- `m4`

Decision:

- If any required LMUL row is missing or not `exact_fit`,
  `formula_fit_for()` reports `partial_fit_blocked`.
- The primary formula fields `base`, `k`, and `residual` remain unset for a
  blocked fit.
- `blocked_lmuls` records the source status and reason for each missing or
  non-exact LMUL row.
- A mathematically possible fit over the exact subset may be retained only as
  `provisional_fit`; it is diagnostic and not an LLVM-facing complete claim.

Current blocked examples:

- `vcpop_m` `ReleaseAtCycles`: `m4` is `non_identifiable`.
- `vrgather_vv` `Latency`: `m4` is `non_identifiable`.
- `vslideup_vx` `Latency`: `m4` is `non_identifiable`.

Replay consequence:

- AC-9 search consistency is restored for formula summaries.
- The search artifact hash changes because the report now records the blocked
  formula status honestly.
- Field-status counts stay unchanged at 141 inferred and 9 non-identifiable.
- AC-16 remains blocked until explicit current-hash-bound human approval exists
  or stronger evidence resolves the 9 non-identifiable rows.
