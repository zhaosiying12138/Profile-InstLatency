# Timing Parameter Search

Status: raw_observation_parameter_search

## Inputs

- trace files before filter: 10411
- trace files after filter: 7220
- usable marker observations: 7216
- profile summaries reference-only: 10
- mode filter: `real_platform_profile`
- backend filter: `gem5_minor`

## Global Assumptions

- Only marker deltas from trace entries are used as calibration evidence.
- Known marker pairs are t0/t1, before/after, start/end, and begin/end; marker_baseline_cycles is subtracted.
- T10/T30 throughput check: marker deltas across repeated stream lengths fit startup + (N - 1) * ReleaseAtCycles.
- T11/T30 RAW-chain check: marker deltas constrain Latency only when body.latency_evidence, body.true_raw_chain, or body.chainable is true.
- T12/T30 consumer-gap checks are recorded by the shared simulator but remain non-identifiable without an explicit bypass/read-advance model.
- T20 pair checks are interpreted as startup+slope groups; a single usable pair count per pair/LMUL cannot identify ProcResource.
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
| `vcpop_m` | `m1` | `Latency` | non_identifiable | `0` | 22 |
| `vcpop_m` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 22 |
| `vcpop_m` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 22 |
| `vcpop_m` | `m1` | `NumMicroOps` | exact_fit | `1` | 22 |
| `vcpop_m` | `m1` | `SingleIssue` | exact_fit | `False` | 22 |
| `vcpop_m` | `m2` | `Latency` | non_identifiable | `0` | 22 |
| `vcpop_m` | `m2` | `ReleaseAtCycles` | exact_fit | `1` | 22 |
| `vcpop_m` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 22 |
| `vcpop_m` | `m2` | `NumMicroOps` | exact_fit | `1` | 22 |
| `vcpop_m` | `m2` | `SingleIssue` | exact_fit | `False` | 22 |
| `vcpop_m` | `m4` | `Latency` | non_identifiable | `n/a` | 84 |
| `vcpop_m` | `m4` | `ReleaseAtCycles` | non_identifiable | `n/a` | 84 |
| `vcpop_m` | `m4` | `ProcResource` | non_identifiable | `n/a` | 84 |
| `vcpop_m` | `m4` | `NumMicroOps` | non_identifiable | `n/a` | 84 |
| `vcpop_m` | `m4` | `SingleIssue` | non_identifiable | `n/a` | 84 |
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
| `viota_m` | `m1` | `Latency` | non_identifiable | `0` | 22 |
| `viota_m` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 22 |
| `viota_m` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 22 |
| `viota_m` | `m1` | `NumMicroOps` | exact_fit | `1` | 22 |
| `viota_m` | `m1` | `SingleIssue` | exact_fit | `False` | 22 |
| `viota_m` | `m2` | `Latency` | non_identifiable | `0` | 22 |
| `viota_m` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 22 |
| `viota_m` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 22 |
| `viota_m` | `m2` | `NumMicroOps` | exact_fit | `1` | 22 |
| `viota_m` | `m2` | `SingleIssue` | exact_fit | `False` | 22 |
| `viota_m` | `m4` | `Latency` | non_identifiable | `0` | 14 |
| `viota_m` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 14 |
| `viota_m` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 14 |
| `viota_m` | `m4` | `NumMicroOps` | exact_fit | `1` | 14 |
| `viota_m` | `m4` | `SingleIssue` | exact_fit | `False` | 14 |
| `vmseq_vv` | `m1` | `Latency` | non_identifiable | `0` | 22 |
| `vmseq_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `5` | 22 |
| `vmseq_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 22 |
| `vmseq_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 22 |
| `vmseq_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 22 |
| `vmseq_vv` | `m2` | `Latency` | non_identifiable | `0` | 22 |
| `vmseq_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `6` | 22 |
| `vmseq_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 22 |
| `vmseq_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 22 |
| `vmseq_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 22 |
| `vmseq_vv` | `m4` | `Latency` | non_identifiable | `0` | 14 |
| `vmseq_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `8` | 14 |
| `vmseq_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 14 |
| `vmseq_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 14 |
| `vmseq_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 14 |
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
| `vrgather_vv` | `m1` | `Latency` | non_identifiable | `0` | 20 |
| `vrgather_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `2` | 20 |
| `vrgather_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 20 |
| `vrgather_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 20 |
| `vrgather_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 20 |
| `vrgather_vv` | `m2` | `Latency` | non_identifiable | `0` | 20 |
| `vrgather_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `6` | 20 |
| `vrgather_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 20 |
| `vrgather_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 20 |
| `vrgather_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 20 |
| `vrgather_vv` | `m4` | `Latency` | non_identifiable | `0` | 14 |
| `vrgather_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `20` | 14 |
| `vrgather_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 14 |
| `vrgather_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 14 |
| `vrgather_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 14 |
| `vslideup_vx` | `m1` | `Latency` | non_identifiable | `0` | 22 |
| `vslideup_vx` | `m1` | `ReleaseAtCycles` | exact_fit | `5` | 22 |
| `vslideup_vx` | `m1` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 22 |
| `vslideup_vx` | `m1` | `NumMicroOps` | exact_fit | `1` | 22 |
| `vslideup_vx` | `m1` | `SingleIssue` | exact_fit | `False` | 22 |
| `vslideup_vx` | `m2` | `Latency` | non_identifiable | `0` | 22 |
| `vslideup_vx` | `m2` | `ReleaseAtCycles` | exact_fit | `7` | 22 |
| `vslideup_vx` | `m2` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 22 |
| `vslideup_vx` | `m2` | `NumMicroOps` | exact_fit | `1` | 22 |
| `vslideup_vx` | `m2` | `SingleIssue` | exact_fit | `False` | 22 |
| `vslideup_vx` | `m4` | `Latency` | non_identifiable | `0` | 14 |
| `vslideup_vx` | `m4` | `ReleaseAtCycles` | exact_fit | `18` | 14 |
| `vslideup_vx` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 14 |
| `vslideup_vx` | `m4` | `NumMicroOps` | exact_fit | `1` | 14 |
| `vslideup_vx` | `m4` | `SingleIssue` | exact_fit | `False` | 14 |
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
| `vcpop_m` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vcpop_m` | `ReleaseAtCycles` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vdivu_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vdivu_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `viota_m` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `viota_m` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vmseq_vv` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vmseq_vv` | `ReleaseAtCycles` | exact_fit | `4 + 1 * LMUL` | 0 |
| `vmul_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vmul_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vredsum_vs` | `Latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vredsum_vs` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vrgather_vv` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vrgather_vv` | `ReleaseAtCycles` | approximate_fit | `0 + 5 * LMUL` | 7 |
| `vslideup_vx` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vslideup_vx` | `ReleaseAtCycles` | approximate_fit | `1 + 4 * LMUL` | 3 |
| `vsll_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vsll_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
