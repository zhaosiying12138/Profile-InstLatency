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
- T10/T30 throughput check: marker deltas across repeated stream lengths fit startup + (N - 1) * ReleaseAtCycles.
- T11/T30 RAW-chain check: marker deltas across repeated chain lengths fit startup + (N - 1) * Latency.
- T12/T30 consumer-gap checks are recorded by the shared simulator but remain non-identifiable without an explicit bypass/read-advance model.
- T20 pair checks are recorded by the shared simulator, but the current single pair-count template cannot separate startup from pipe overlap.
- T21 scalar-pair checks are evaluated inside the same candidate tuple and assume a one-cycle scalar issue companion.
- trace.synthetic and generated profile.yaml timing claims are reference-only and are not used as evidence.

## Warnings

- results/r01/common/experiments/t00-marker/trace.json: missing instruction_id, lmul, or template_id
- results/r01/common/experiments/t40-common-vlsu-load-hit-m1/trace.json: missing instruction_id, lmul, or template_id
- results/r02/common/experiments/t00-marker/trace.json: missing instruction_id, lmul, or template_id
- results/r02/common/experiments/t40-common-vlsu-load-hit-m1/trace.json: missing instruction_id, lmul, or template_id

## Candidates

| Instruction | LMUL | Field | Status | Candidate | Evidence |
| --- | --- | --- | --- | --- | ---: |
| `vadd_vv` | `m1` | `Latency` | exact_fit | `4` | 42 |
| `vadd_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 42 |
| `vadd_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vadd_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vadd_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 42 |
| `vadd_vv` | `m2` | `Latency` | exact_fit | `4` | 42 |
| `vadd_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 42 |
| `vadd_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vadd_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vadd_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 42 |
| `vadd_vv` | `m4` | `Latency` | exact_fit | `4` | 34 |
| `vadd_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 34 |
| `vadd_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 34 |
| `vadd_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 34 |
| `vadd_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 34 |
| `vcpop_m` | `m1` | `Latency` | exact_fit | `1` | 42 |
| `vcpop_m` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 42 |
| `vcpop_m` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vcpop_m` | `m1` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vcpop_m` | `m1` | `SingleIssue` | exact_fit | `False` | 42 |
| `vcpop_m` | `m2` | `Latency` | exact_fit | `1` | 42 |
| `vcpop_m` | `m2` | `ReleaseAtCycles` | exact_fit | `1` | 42 |
| `vcpop_m` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vcpop_m` | `m2` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vcpop_m` | `m2` | `SingleIssue` | exact_fit | `False` | 42 |
| `vcpop_m` | `m4` | `Latency` | conflict | `n/a` | 50 |
| `vcpop_m` | `m4` | `ReleaseAtCycles` | conflict | `n/a` | 50 |
| `vcpop_m` | `m4` | `ProcResource` | conflict | `n/a` | 50 |
| `vcpop_m` | `m4` | `NumMicroOps` | conflict | `n/a` | 50 |
| `vcpop_m` | `m4` | `SingleIssue` | conflict | `n/a` | 50 |
| `vdivu_vv` | `m1` | `Latency` | exact_fit | `4` | 42 |
| `vdivu_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 42 |
| `vdivu_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vdivu_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vdivu_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 42 |
| `vdivu_vv` | `m2` | `Latency` | exact_fit | `4` | 42 |
| `vdivu_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 42 |
| `vdivu_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vdivu_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vdivu_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 42 |
| `vdivu_vv` | `m4` | `Latency` | exact_fit | `4` | 34 |
| `vdivu_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 34 |
| `vdivu_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 34 |
| `vdivu_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 34 |
| `vdivu_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 34 |
| `viota_m` | `m1` | `Latency` | exact_fit | `1` | 42 |
| `viota_m` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 42 |
| `viota_m` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `viota_m` | `m1` | `NumMicroOps` | exact_fit | `1` | 42 |
| `viota_m` | `m1` | `SingleIssue` | exact_fit | `False` | 42 |
| `viota_m` | `m2` | `Latency` | exact_fit | `2` | 42 |
| `viota_m` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 42 |
| `viota_m` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `viota_m` | `m2` | `NumMicroOps` | exact_fit | `1` | 42 |
| `viota_m` | `m2` | `SingleIssue` | exact_fit | `False` | 42 |
| `viota_m` | `m4` | `Latency` | exact_fit | `4` | 34 |
| `viota_m` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 34 |
| `viota_m` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 34 |
| `viota_m` | `m4` | `NumMicroOps` | exact_fit | `1` | 34 |
| `viota_m` | `m4` | `SingleIssue` | exact_fit | `False` | 34 |
| `vmseq_vv` | `m1` | `Latency` | exact_fit | `5` | 42 |
| `vmseq_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `5` | 42 |
| `vmseq_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vmseq_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vmseq_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 42 |
| `vmseq_vv` | `m2` | `Latency` | exact_fit | `6` | 42 |
| `vmseq_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `6` | 42 |
| `vmseq_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vmseq_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vmseq_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 42 |
| `vmseq_vv` | `m4` | `Latency` | exact_fit | `8` | 34 |
| `vmseq_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `8` | 34 |
| `vmseq_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 34 |
| `vmseq_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 34 |
| `vmseq_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 34 |
| `vmul_vv` | `m1` | `Latency` | exact_fit | `4` | 42 |
| `vmul_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 42 |
| `vmul_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vmul_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vmul_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 42 |
| `vmul_vv` | `m2` | `Latency` | exact_fit | `4` | 42 |
| `vmul_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 42 |
| `vmul_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vmul_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vmul_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 42 |
| `vmul_vv` | `m4` | `Latency` | exact_fit | `4` | 34 |
| `vmul_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 34 |
| `vmul_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 34 |
| `vmul_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 34 |
| `vmul_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 34 |
| `vredsum_vs` | `m1` | `Latency` | exact_fit | `4` | 42 |
| `vredsum_vs` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 42 |
| `vredsum_vs` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vredsum_vs` | `m1` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vredsum_vs` | `m1` | `SingleIssue` | exact_fit | `False` | 42 |
| `vredsum_vs` | `m2` | `Latency` | exact_fit | `5` | 42 |
| `vredsum_vs` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 42 |
| `vredsum_vs` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vredsum_vs` | `m2` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vredsum_vs` | `m2` | `SingleIssue` | exact_fit | `False` | 42 |
| `vredsum_vs` | `m4` | `Latency` | exact_fit | `7` | 34 |
| `vredsum_vs` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 34 |
| `vredsum_vs` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 34 |
| `vredsum_vs` | `m4` | `NumMicroOps` | exact_fit | `1` | 34 |
| `vredsum_vs` | `m4` | `SingleIssue` | exact_fit | `False` | 34 |
| `vrgather_vv` | `m1` | `Latency` | exact_fit | `2` | 40 |
| `vrgather_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `2` | 40 |
| `vrgather_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 40 |
| `vrgather_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 40 |
| `vrgather_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 40 |
| `vrgather_vv` | `m2` | `Latency` | exact_fit | `6` | 40 |
| `vrgather_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `6` | 40 |
| `vrgather_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 40 |
| `vrgather_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 40 |
| `vrgather_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 40 |
| `vrgather_vv` | `m4` | `Latency` | exact_fit | `20` | 34 |
| `vrgather_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `20` | 34 |
| `vrgather_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 34 |
| `vrgather_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 34 |
| `vrgather_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 34 |
| `vslideup_vx` | `m1` | `Latency` | exact_fit | `5` | 42 |
| `vslideup_vx` | `m1` | `ReleaseAtCycles` | exact_fit | `5` | 42 |
| `vslideup_vx` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vslideup_vx` | `m1` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vslideup_vx` | `m1` | `SingleIssue` | exact_fit | `False` | 42 |
| `vslideup_vx` | `m2` | `Latency` | exact_fit | `7` | 42 |
| `vslideup_vx` | `m2` | `ReleaseAtCycles` | exact_fit | `7` | 42 |
| `vslideup_vx` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vslideup_vx` | `m2` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vslideup_vx` | `m2` | `SingleIssue` | exact_fit | `False` | 42 |
| `vslideup_vx` | `m4` | `Latency` | exact_fit | `18` | 34 |
| `vslideup_vx` | `m4` | `ReleaseAtCycles` | exact_fit | `18` | 34 |
| `vslideup_vx` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 34 |
| `vslideup_vx` | `m4` | `NumMicroOps` | exact_fit | `1` | 34 |
| `vslideup_vx` | `m4` | `SingleIssue` | exact_fit | `False` | 34 |
| `vsll_vv` | `m1` | `Latency` | exact_fit | `4` | 42 |
| `vsll_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 42 |
| `vsll_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vsll_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vsll_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 42 |
| `vsll_vv` | `m2` | `Latency` | exact_fit | `4` | 42 |
| `vsll_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 42 |
| `vsll_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 42 |
| `vsll_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 42 |
| `vsll_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 42 |
| `vsll_vv` | `m4` | `Latency` | exact_fit | `4` | 34 |
| `vsll_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 34 |
| `vsll_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 34 |
| `vsll_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 34 |
| `vsll_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 34 |

## Formula Fits

| Instruction | Field | Status | Formula | Residual |
| --- | --- | --- | --- | ---: |
| `vadd_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vadd_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vcpop_m` | `Latency` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vcpop_m` | `ReleaseAtCycles` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vdivu_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vdivu_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `viota_m` | `Latency` | exact_fit | `0 + 1 * LMUL` | 0 |
| `viota_m` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vmseq_vv` | `Latency` | exact_fit | `4 + 1 * LMUL` | 0 |
| `vmseq_vv` | `ReleaseAtCycles` | exact_fit | `4 + 1 * LMUL` | 0 |
| `vmul_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vmul_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vredsum_vs` | `Latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vredsum_vs` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vrgather_vv` | `Latency` | approximate_fit | `0 + 5 * LMUL` | 7 |
| `vrgather_vv` | `ReleaseAtCycles` | approximate_fit | `0 + 5 * LMUL` | 7 |
| `vslideup_vx` | `Latency` | approximate_fit | `1 + 4 * LMUL` | 3 |
| `vslideup_vx` | `ReleaseAtCycles` | approximate_fit | `1 + 4 * LMUL` | 3 |
| `vsll_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vsll_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
