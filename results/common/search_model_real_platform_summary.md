# Timing Parameter Search

Status: raw_observation_parameter_search

## Inputs

- trace files before filter: 9663
- trace files after filter: 6472
- usable marker observations: 6468
- profile summaries reference-only: 10
- mode filter: `real_platform_profile`
- backend filter: `gem5_minor`

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

- results/r01/common/experiments/t00-marker/trace.json: missing instruction_id, lmul, or template_id
- results/r01/common/experiments/t40-common-vlsu-load-hit-m1/trace.json: missing instruction_id, lmul, or template_id
- results/r02/common/experiments/t00-marker/trace.json: missing instruction_id, lmul, or template_id
- results/r02/common/experiments/t40-common-vlsu-load-hit-m1/trace.json: missing instruction_id, lmul, or template_id

## Candidates

| Instruction | LMUL | Field | Status | Candidate | Evidence |
| --- | --- | --- | --- | --- | ---: |
| `vadd_vv` | `m1` | `Latency` | exact_fit | `4` | 20 |
| `vadd_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 20 |
| `vadd_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vadd_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 2 |
| `vadd_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 2 |
| `vadd_vv` | `m2` | `Latency` | conflict | `n/a` | 20 |
| `vadd_vv` | `m2` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vadd_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vadd_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vadd_vv` | `m2` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vadd_vv` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `vadd_vv` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 12 |
| `vadd_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vadd_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vadd_vv` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vcpop_m` | `m1` | `Latency` | exact_fit | `1` | 20 |
| `vcpop_m` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 20 |
| `vcpop_m` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vcpop_m` | `m1` | `NumMicroOps` | exact_fit | `1` | 2 |
| `vcpop_m` | `m1` | `SingleIssue` | exact_fit | `False` | 2 |
| `vcpop_m` | `m2` | `Latency` | exact_fit | `1` | 20 |
| `vcpop_m` | `m2` | `ReleaseAtCycles` | exact_fit | `1` | 20 |
| `vcpop_m` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vcpop_m` | `m2` | `NumMicroOps` | exact_fit | `1` | 2 |
| `vcpop_m` | `m2` | `SingleIssue` | exact_fit | `False` | 2 |
| `vcpop_m` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `vcpop_m` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vcpop_m` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vcpop_m` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vcpop_m` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vdivu_vv` | `m1` | `Latency` | exact_fit | `4` | 20 |
| `vdivu_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 20 |
| `vdivu_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vdivu_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 2 |
| `vdivu_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 2 |
| `vdivu_vv` | `m2` | `Latency` | conflict | `n/a` | 20 |
| `vdivu_vv` | `m2` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vdivu_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vdivu_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vdivu_vv` | `m2` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vdivu_vv` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `vdivu_vv` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 12 |
| `vdivu_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vdivu_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vdivu_vv` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `viota_m` | `m1` | `Latency` | exact_fit | `1` | 20 |
| `viota_m` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 20 |
| `viota_m` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `viota_m` | `m1` | `NumMicroOps` | exact_fit | `1` | 2 |
| `viota_m` | `m1` | `SingleIssue` | exact_fit | `False` | 2 |
| `viota_m` | `m2` | `Latency` | conflict | `n/a` | 20 |
| `viota_m` | `m2` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `viota_m` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `viota_m` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `viota_m` | `m2` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `viota_m` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `viota_m` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 12 |
| `viota_m` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `viota_m` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `viota_m` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vmseq_vv` | `m1` | `Latency` | conflict | `n/a` | 20 |
| `vmseq_vv` | `m1` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vmseq_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmseq_vv` | `m1` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vmseq_vv` | `m1` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vmseq_vv` | `m2` | `Latency` | conflict | `n/a` | 20 |
| `vmseq_vv` | `m2` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vmseq_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmseq_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vmseq_vv` | `m2` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vmseq_vv` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `vmseq_vv` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 12 |
| `vmseq_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmseq_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vmseq_vv` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vmul_vv` | `m1` | `Latency` | exact_fit | `4` | 20 |
| `vmul_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 20 |
| `vmul_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmul_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 2 |
| `vmul_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 2 |
| `vmul_vv` | `m2` | `Latency` | conflict | `n/a` | 20 |
| `vmul_vv` | `m2` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vmul_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmul_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vmul_vv` | `m2` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vmul_vv` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `vmul_vv` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 12 |
| `vmul_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vmul_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vmul_vv` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vredsum_vs` | `m1` | `Latency` | exact_fit | `4` | 20 |
| `vredsum_vs` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 20 |
| `vredsum_vs` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vredsum_vs` | `m1` | `NumMicroOps` | exact_fit | `1` | 2 |
| `vredsum_vs` | `m1` | `SingleIssue` | exact_fit | `False` | 2 |
| `vredsum_vs` | `m2` | `Latency` | conflict | `n/a` | 20 |
| `vredsum_vs` | `m2` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vredsum_vs` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vredsum_vs` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vredsum_vs` | `m2` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vredsum_vs` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `vredsum_vs` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 12 |
| `vredsum_vs` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vredsum_vs` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vredsum_vs` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vrgather_vv` | `m1` | `Latency` | conflict | `n/a` | 20 |
| `vrgather_vv` | `m1` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vrgather_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vrgather_vv` | `m1` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vrgather_vv` | `m1` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vrgather_vv` | `m2` | `Latency` | conflict | `n/a` | 20 |
| `vrgather_vv` | `m2` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vrgather_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vrgather_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vrgather_vv` | `m2` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vrgather_vv` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `vrgather_vv` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 12 |
| `vrgather_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vrgather_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vrgather_vv` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vslideup_vx` | `m1` | `Latency` | conflict | `n/a` | 20 |
| `vslideup_vx` | `m1` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vslideup_vx` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vslideup_vx` | `m1` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vslideup_vx` | `m1` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vslideup_vx` | `m2` | `Latency` | conflict | `n/a` | 20 |
| `vslideup_vx` | `m2` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vslideup_vx` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vslideup_vx` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vslideup_vx` | `m2` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vslideup_vx` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `vslideup_vx` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 12 |
| `vslideup_vx` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vslideup_vx` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vslideup_vx` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vsll_vv` | `m1` | `Latency` | exact_fit | `4` | 20 |
| `vsll_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 20 |
| `vsll_vv` | `m1` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vsll_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 2 |
| `vsll_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 2 |
| `vsll_vv` | `m2` | `Latency` | conflict | `n/a` | 20 |
| `vsll_vv` | `m2` | `ReleaseAtCycles` | conflict | `n/a` | 20 |
| `vsll_vv` | `m2` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vsll_vv` | `m2` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vsll_vv` | `m2` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |
| `vsll_vv` | `m4` | `Latency` | conflict | `n/a` | 20 |
| `vsll_vv` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 12 |
| `vsll_vv` | `m4` | `ProcResource` | insufficient_evidence | `unknown` | 0 |
| `vsll_vv` | `m4` | `NumMicroOps` | insufficient_evidence | `1, 2, 3, 4` | 0 |
| `vsll_vv` | `m4` | `SingleIssue` | insufficient_evidence | `False, True` | 0 |

## Formula Fits

| Instruction | Field | Status | Formula | Residual |
| --- | --- | --- | --- | ---: |
| `vadd_vv` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vadd_vv` | `ReleaseAtCycles` | insufficient_evidence | `n/a` | n/a |
| `vcpop_m` | `Latency` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vcpop_m` | `ReleaseAtCycles` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vdivu_vv` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vdivu_vv` | `ReleaseAtCycles` | insufficient_evidence | `n/a` | n/a |
| `viota_m` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `viota_m` | `ReleaseAtCycles` | insufficient_evidence | `n/a` | n/a |
| `vmseq_vv` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vmseq_vv` | `ReleaseAtCycles` | insufficient_evidence | `n/a` | n/a |
| `vmul_vv` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vmul_vv` | `ReleaseAtCycles` | insufficient_evidence | `n/a` | n/a |
| `vredsum_vs` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vredsum_vs` | `ReleaseAtCycles` | insufficient_evidence | `n/a` | n/a |
| `vrgather_vv` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vrgather_vv` | `ReleaseAtCycles` | insufficient_evidence | `n/a` | n/a |
| `vslideup_vx` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vslideup_vx` | `ReleaseAtCycles` | insufficient_evidence | `n/a` | n/a |
| `vsll_vv` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vsll_vv` | `ReleaseAtCycles` | insufficient_evidence | `n/a` | n/a |
