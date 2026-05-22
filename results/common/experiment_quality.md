# Experiment Quality Report

Mode: real_platform_profile
Gate status: NOT_READY
Human approval status: absent

This report is intentionally separate from synthetic golden matching. The current data set is synthetic dry-run evidence only, so the real-platform gate remains closed.

## Coverage

Result root: `results`
Trace files analyzed: 407
Synthetic traces analyzed: 407
Instruction/LMUL pairs covered: 30

| Instruction | Covered LMULs |
| --- | --- |
| `vadd_vv` | `m1, m2, m4` |
| `vcpop_m` | `m1, m2, m4` |
| `vdivu_vv` | `m1, m2, m4` |
| `viota_m` | `m1, m2, m4` |
| `vmseq_vv` | `m1, m2, m4` |
| `vmul_vv` | `m1, m2, m4` |
| `vredsum_vs` | `m1, m2, m4` |
| `vrgather_vv` | `m1, m2, m4` |
| `vslideup_vx` | `m1, m2, m4` |
| `vsll_vv` | `m1, m2, m4` |

## Stability

Synthetic primary delta mean: 16.980 cycles.
No repeated real-platform measurements are available; stability is not established.

## Confidence

Confidence for the real-platform profile is insufficient because current evidence is synthetic metadata, not hardware or gem5 timing output.

## Assumptions

- Synthetic timestamp markers are treated as zero-cost observations after subtracting marker_baseline_cycles.
- Processor issue width and real resource contention are not approved from this dry-run data.
- Real platform mode must not use golden equality as an exit condition.

## Human Approval

Human approval is absent. To pass, a future real-platform report must set an explicit approval status after coverage, stability, confidence, assumptions, and conflicts are reviewed.
