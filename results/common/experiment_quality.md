# Experiment Quality Report

Mode: real_platform_profile
Gate status: NOT_READY
Human approval status: absent

This report is intentionally separate from synthetic golden matching. The current data set combines synthetic calibration traces with a gem5 MinorCPU decode/execute kill-check, so the real-platform gate remains closed until the full latency/resource experiment suite has real repeated coverage and human approval.

## Coverage

Result root: `results`
Trace files analyzed: 3221
Synthetic traces analyzed: 3191
Real-platform traces analyzed: 30
Real-platform template coverage: T01_DECODE_EXEC_KILLCHECK
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

Synthetic primary delta mean: 28.826 cycles.
No repeated full-suite real-platform measurements are available; stability is not established.

## Confidence

Confidence for the real-platform profile is insufficient because gem5 evidence currently covers only the T01 decode/execute kill-check. LLVM-facing latency, release, and pipe-resource claims still come from non-circular synthetic calibration traces.

## Assumptions

- Synthetic timestamp markers are treated as zero-cost observations after subtracting marker_baseline_cycles.
- T01 gem5 traces prove the selected RVV instructions assemble, link, decode, and execute under the configured MinorCPU backend.
- Processor issue width and real resource contention are not approved from this partial real-platform data.
- Real platform mode must not use golden equality as an exit condition.

## Human Approval

Human approval is absent. To pass, a future real-platform report must set an explicit approval status after coverage, stability, confidence, assumptions, and conflicts are reviewed.
