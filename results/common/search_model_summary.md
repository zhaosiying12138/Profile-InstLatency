# Timing Parameter Search

Status: raw_observation_parameter_search

## Inputs

- trace files: 3221
- usable marker observations: 3219
- profile summaries reference-only: 10

## Global Assumptions

- Only marker deltas from trace entries are used as calibration evidence.
- Known marker pairs are t0/t1, before/after, start/end, and begin/end; marker_baseline_cycles is subtracted.
- T10/T30 throughput check: delta_cycles == iterations * ReleaseAtCycles.
- T11/T30 RAW-chain check: delta_cycles == iterations * Latency.
- T12/T30 consumer-gap check: delta_cycles == filler_count + Latency.
- T20 pair checks compare pair cycles with already identified per-instruction ReleaseAtCycles.
- T21 scalar-pair checks assume a one-cycle scalar issue companion; ambiguous NumMicroOps/SingleIssue cases stay insufficient_evidence.
- trace.synthetic and generated profile.yaml timing claims are reference-only and are not used as evidence.

## Warnings

- results/common/experiments/t00-marker/trace.json: missing instruction_id, lmul, or template_id
- results/common/experiments/t40-common-vlsu-load-hit-m1/trace.json: missing instruction_id, lmul, or template_id

## Candidates

| Instruction | LMUL | Field | Status | Candidate | Evidence |
| --- | --- | --- | --- | --- | ---: |
| `vadd_vv` | `m1` | `Latency` | exact_fit | `2` | 92 |
| `vadd_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 10 |
| `vadd_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vadd_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vadd_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `vadd_vv` | `m2` | `Latency` | exact_fit | `2` | 92 |
| `vadd_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `1` | 10 |
| `vadd_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vadd_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vadd_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `vadd_vv` | `m4` | `Latency` | exact_fit | `2` | 92 |
| `vadd_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `1` | 6 |
| `vadd_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vadd_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vadd_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |
| `vcpop_m` | `m1` | `Latency` | exact_fit | `4` | 92 |
| `vcpop_m` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 10 |
| `vcpop_m` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vcpop_m` | `m1` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vcpop_m` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `vcpop_m` | `m2` | `Latency` | exact_fit | `5` | 92 |
| `vcpop_m` | `m2` | `ReleaseAtCycles` | exact_fit | `1` | 10 |
| `vcpop_m` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vcpop_m` | `m2` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vcpop_m` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `vcpop_m` | `m4` | `Latency` | exact_fit | `7` | 92 |
| `vcpop_m` | `m4` | `ReleaseAtCycles` | exact_fit | `1` | 10 |
| `vcpop_m` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vcpop_m` | `m4` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vcpop_m` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |
| `vdivu_vv` | `m1` | `Latency` | exact_fit | `18` | 92 |
| `vdivu_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `6` | 10 |
| `vdivu_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vdivu_vv` | `m1` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 1 |
| `vdivu_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `vdivu_vv` | `m2` | `Latency` | exact_fit | `24` | 92 |
| `vdivu_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `8` | 10 |
| `vdivu_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vdivu_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 1 |
| `vdivu_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `vdivu_vv` | `m4` | `Latency` | exact_fit | `36` | 92 |
| `vdivu_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `12` | 6 |
| `vdivu_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vdivu_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 1 |
| `vdivu_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |
| `viota_m` | `m1` | `Latency` | exact_fit | `6` | 92 |
| `viota_m` | `m1` | `ReleaseAtCycles` | exact_fit | `2` | 10 |
| `viota_m` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `viota_m` | `m1` | `NumMicroOps` | insufficient_evidence | `1, 2` | 1 |
| `viota_m` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `viota_m` | `m2` | `Latency` | exact_fit | `8` | 92 |
| `viota_m` | `m2` | `ReleaseAtCycles` | exact_fit | `3` | 10 |
| `viota_m` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `viota_m` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3` | 1 |
| `viota_m` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `viota_m` | `m4` | `Latency` | exact_fit | `12` | 92 |
| `viota_m` | `m4` | `ReleaseAtCycles` | exact_fit | `5` | 6 |
| `viota_m` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `viota_m` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 1 |
| `viota_m` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |
| `vmseq_vv` | `m1` | `Latency` | exact_fit | `2` | 92 |
| `vmseq_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 10 |
| `vmseq_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmseq_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vmseq_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `vmseq_vv` | `m2` | `Latency` | exact_fit | `2` | 92 |
| `vmseq_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `1` | 10 |
| `vmseq_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmseq_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vmseq_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `vmseq_vv` | `m4` | `Latency` | exact_fit | `2` | 92 |
| `vmseq_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `1` | 6 |
| `vmseq_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmseq_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vmseq_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |
| `vmul_vv` | `m1` | `Latency` | exact_fit | `6` | 92 |
| `vmul_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `2` | 10 |
| `vmul_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmul_vv` | `m1` | `NumMicroOps` | insufficient_evidence | `1, 2` | 1 |
| `vmul_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `vmul_vv` | `m2` | `Latency` | exact_fit | `7` | 92 |
| `vmul_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `3` | 10 |
| `vmul_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmul_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3` | 1 |
| `vmul_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `vmul_vv` | `m4` | `Latency` | exact_fit | `9` | 92 |
| `vmul_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `5` | 6 |
| `vmul_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmul_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 1 |
| `vmul_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |
| `vredsum_vs` | `m1` | `Latency` | exact_fit | `9` | 92 |
| `vredsum_vs` | `m1` | `ReleaseAtCycles` | exact_fit | `2` | 10 |
| `vredsum_vs` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vredsum_vs` | `m1` | `NumMicroOps` | insufficient_evidence | `1, 2` | 1 |
| `vredsum_vs` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `vredsum_vs` | `m2` | `Latency` | exact_fit | `12` | 92 |
| `vredsum_vs` | `m2` | `ReleaseAtCycles` | exact_fit | `3` | 10 |
| `vredsum_vs` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vredsum_vs` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3` | 1 |
| `vredsum_vs` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `vredsum_vs` | `m4` | `Latency` | exact_fit | `18` | 92 |
| `vredsum_vs` | `m4` | `ReleaseAtCycles` | exact_fit | `5` | 6 |
| `vredsum_vs` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vredsum_vs` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 1 |
| `vredsum_vs` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |
| `vrgather_vv` | `m1` | `Latency` | exact_fit | `7` | 92 |
| `vrgather_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `2` | 10 |
| `vrgather_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vrgather_vv` | `m1` | `NumMicroOps` | insufficient_evidence | `1, 2` | 1 |
| `vrgather_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `vrgather_vv` | `m2` | `Latency` | exact_fit | `9` | 92 |
| `vrgather_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `3` | 10 |
| `vrgather_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vrgather_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3` | 1 |
| `vrgather_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `vrgather_vv` | `m4` | `Latency` | exact_fit | `13` | 92 |
| `vrgather_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `5` | 6 |
| `vrgather_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vrgather_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 1 |
| `vrgather_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |
| `vslideup_vx` | `m1` | `Latency` | exact_fit | `4` | 92 |
| `vslideup_vx` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 10 |
| `vslideup_vx` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vslideup_vx` | `m1` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vslideup_vx` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `vslideup_vx` | `m2` | `Latency` | exact_fit | `5` | 92 |
| `vslideup_vx` | `m2` | `ReleaseAtCycles` | exact_fit | `1` | 10 |
| `vslideup_vx` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vslideup_vx` | `m2` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vslideup_vx` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `vslideup_vx` | `m4` | `Latency` | exact_fit | `7` | 92 |
| `vslideup_vx` | `m4` | `ReleaseAtCycles` | exact_fit | `1` | 6 |
| `vslideup_vx` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vslideup_vx` | `m4` | `NumMicroOps` | exact_fit | `1` | 1 |
| `vslideup_vx` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |
| `vsll_vv` | `m1` | `Latency` | exact_fit | `4` | 92 |
| `vsll_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `2` | 10 |
| `vsll_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vsll_vv` | `m1` | `NumMicroOps` | insufficient_evidence | `1, 2` | 1 |
| `vsll_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 1 |
| `vsll_vv` | `m2` | `Latency` | exact_fit | `5` | 92 |
| `vsll_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `3` | 10 |
| `vsll_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vsll_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3` | 1 |
| `vsll_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 1 |
| `vsll_vv` | `m4` | `Latency` | exact_fit | `7` | 92 |
| `vsll_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `5` | 6 |
| `vsll_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vsll_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 1 |
| `vsll_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 1 |

## Formula Fits

| Instruction | Field | Status | Formula | Residual |
| --- | --- | --- | --- | ---: |
| `vadd_vv` | `Latency` | exact_fit | `2 + 0 * LMUL` | 0 |
| `vadd_vv` | `ReleaseAtCycles` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vcpop_m` | `Latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vcpop_m` | `ReleaseAtCycles` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vdivu_vv` | `Latency` | exact_fit | `12 + 6 * LMUL` | 0 |
| `vdivu_vv` | `ReleaseAtCycles` | exact_fit | `4 + 2 * LMUL` | 0 |
| `viota_m` | `Latency` | exact_fit | `4 + 2 * LMUL` | 0 |
| `viota_m` | `ReleaseAtCycles` | exact_fit | `1 + 1 * LMUL` | 0 |
| `vmseq_vv` | `Latency` | exact_fit | `2 + 0 * LMUL` | 0 |
| `vmseq_vv` | `ReleaseAtCycles` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vmul_vv` | `Latency` | exact_fit | `5 + 1 * LMUL` | 0 |
| `vmul_vv` | `ReleaseAtCycles` | exact_fit | `1 + 1 * LMUL` | 0 |
| `vredsum_vs` | `Latency` | exact_fit | `6 + 3 * LMUL` | 0 |
| `vredsum_vs` | `ReleaseAtCycles` | exact_fit | `1 + 1 * LMUL` | 0 |
| `vrgather_vv` | `Latency` | exact_fit | `5 + 2 * LMUL` | 0 |
| `vrgather_vv` | `ReleaseAtCycles` | exact_fit | `1 + 1 * LMUL` | 0 |
| `vslideup_vx` | `Latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vslideup_vx` | `ReleaseAtCycles` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vsll_vv` | `Latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vsll_vv` | `ReleaseAtCycles` | exact_fit | `1 + 1 * LMUL` | 0 |
