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
- T12/T30 consumer-gap checks use a conservative clean-prefix filler-cadence model to infer exact latency or upper-bound constraints.
- T20 pair checks are interpreted as startup-free slope groups; a single usable pair count per pair/LMUL cannot identify ProcResource.
- Global ProcResource solving uses only clean startup-free T20 pair slopes plus exact ReleaseAtCycles values; constraints with missing or empty peer domains are skipped.
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
| `vadd_vv` | `m1` | `Latency` | exact_fit | `4` | 166 |
| `vadd_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 166 |
| `vadd_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vadd_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vadd_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 166 |
| `vadd_vv` | `m2` | `Latency` | exact_fit | `4` | 166 |
| `vadd_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 166 |
| `vadd_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vadd_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vadd_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 166 |
| `vadd_vv` | `m4` | `Latency` | exact_fit | `4` | 198 |
| `vadd_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 198 |
| `vadd_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 198 |
| `vadd_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 198 |
| `vadd_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 198 |
| `vcpop_m` | `m1` | `Latency` | non_identifiable | `0, 1` | 146 |
| `vcpop_m` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 146 |
| `vcpop_m` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vcpop_m` | `m1` | `NumMicroOps` | exact_fit | `1` | 146 |
| `vcpop_m` | `m1` | `SingleIssue` | exact_fit | `False` | 146 |
| `vcpop_m` | `m2` | `Latency` | non_identifiable | `0, 1, 2` | 146 |
| `vcpop_m` | `m2` | `ReleaseAtCycles` | exact_fit | `1` | 146 |
| `vcpop_m` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vcpop_m` | `m2` | `NumMicroOps` | exact_fit | `1` | 146 |
| `vcpop_m` | `m2` | `SingleIssue` | exact_fit | `False` | 146 |
| `vcpop_m` | `m4` | `Latency` | non_identifiable | `0, 1, 2, 3, 4` | 288 |
| `vcpop_m` | `m4` | `ReleaseAtCycles` | non_identifiable | `n/a` | 288 |
| `vcpop_m` | `m4` | `ProcResource` | non_identifiable | `n/a` | 288 |
| `vcpop_m` | `m4` | `NumMicroOps` | non_identifiable | `n/a` | 288 |
| `vcpop_m` | `m4` | `SingleIssue` | non_identifiable | `n/a` | 288 |
| `vdivu_vv` | `m1` | `Latency` | exact_fit | `4` | 166 |
| `vdivu_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 166 |
| `vdivu_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vdivu_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vdivu_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 166 |
| `vdivu_vv` | `m2` | `Latency` | exact_fit | `4` | 166 |
| `vdivu_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 166 |
| `vdivu_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vdivu_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vdivu_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 166 |
| `vdivu_vv` | `m4` | `Latency` | exact_fit | `4` | 198 |
| `vdivu_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 198 |
| `vdivu_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 198 |
| `vdivu_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 198 |
| `vdivu_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 198 |
| `viota_m` | `m1` | `Latency` | exact_fit | `4` | 146 |
| `viota_m` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 146 |
| `viota_m` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `viota_m` | `m1` | `NumMicroOps` | exact_fit | `1` | 146 |
| `viota_m` | `m1` | `SingleIssue` | exact_fit | `False` | 146 |
| `viota_m` | `m2` | `Latency` | exact_fit | `4` | 146 |
| `viota_m` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 146 |
| `viota_m` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `viota_m` | `m2` | `NumMicroOps` | exact_fit | `1` | 146 |
| `viota_m` | `m2` | `SingleIssue` | exact_fit | `False` | 146 |
| `viota_m` | `m4` | `Latency` | non_identifiable | `0, 1, 2, 3, 4` | 178 |
| `viota_m` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 178 |
| `viota_m` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 178 |
| `viota_m` | `m4` | `NumMicroOps` | exact_fit | `1` | 178 |
| `viota_m` | `m4` | `SingleIssue` | exact_fit | `False` | 178 |
| `vmseq_vv` | `m1` | `Latency` | exact_fit | `4` | 146 |
| `vmseq_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `5` | 146 |
| `vmseq_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vmseq_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 146 |
| `vmseq_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 146 |
| `vmseq_vv` | `m2` | `Latency` | exact_fit | `5` | 146 |
| `vmseq_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `6` | 146 |
| `vmseq_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vmseq_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 146 |
| `vmseq_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 146 |
| `vmseq_vv` | `m4` | `Latency` | exact_fit | `7` | 178 |
| `vmseq_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `8` | 178 |
| `vmseq_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 178 |
| `vmseq_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 178 |
| `vmseq_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 178 |
| `vmul_vv` | `m1` | `Latency` | exact_fit | `4` | 166 |
| `vmul_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 166 |
| `vmul_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vmul_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vmul_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 166 |
| `vmul_vv` | `m2` | `Latency` | exact_fit | `4` | 166 |
| `vmul_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 166 |
| `vmul_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vmul_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vmul_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 166 |
| `vmul_vv` | `m4` | `Latency` | exact_fit | `4` | 198 |
| `vmul_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 198 |
| `vmul_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 198 |
| `vmul_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 198 |
| `vmul_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 198 |
| `vredsum_vs` | `m1` | `Latency` | exact_fit | `4` | 166 |
| `vredsum_vs` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 166 |
| `vredsum_vs` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vredsum_vs` | `m1` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vredsum_vs` | `m1` | `SingleIssue` | exact_fit | `False` | 166 |
| `vredsum_vs` | `m2` | `Latency` | exact_fit | `5` | 166 |
| `vredsum_vs` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 166 |
| `vredsum_vs` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vredsum_vs` | `m2` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vredsum_vs` | `m2` | `SingleIssue` | exact_fit | `False` | 166 |
| `vredsum_vs` | `m4` | `Latency` | exact_fit | `7` | 198 |
| `vredsum_vs` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 198 |
| `vredsum_vs` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 198 |
| `vredsum_vs` | `m4` | `NumMicroOps` | exact_fit | `1` | 198 |
| `vredsum_vs` | `m4` | `SingleIssue` | exact_fit | `False` | 198 |
| `vrgather_vv` | `m1` | `Latency` | exact_fit | `4` | 144 |
| `vrgather_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `2` | 144 |
| `vrgather_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vrgather_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 144 |
| `vrgather_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 144 |
| `vrgather_vv` | `m2` | `Latency` | exact_fit | `4` | 144 |
| `vrgather_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `6` | 144 |
| `vrgather_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vrgather_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 144 |
| `vrgather_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 144 |
| `vrgather_vv` | `m4` | `Latency` | non_identifiable | `0, 1, 2, 3, 4` | 178 |
| `vrgather_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `20` | 178 |
| `vrgather_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 178 |
| `vrgather_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 178 |
| `vrgather_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 178 |
| `vslideup_vx` | `m1` | `Latency` | exact_fit | `4` | 146 |
| `vslideup_vx` | `m1` | `ReleaseAtCycles` | exact_fit | `5` | 146 |
| `vslideup_vx` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vslideup_vx` | `m1` | `NumMicroOps` | exact_fit | `1` | 146 |
| `vslideup_vx` | `m1` | `SingleIssue` | exact_fit | `False` | 146 |
| `vslideup_vx` | `m2` | `Latency` | exact_fit | `4` | 146 |
| `vslideup_vx` | `m2` | `ReleaseAtCycles` | exact_fit | `7` | 146 |
| `vslideup_vx` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vslideup_vx` | `m2` | `NumMicroOps` | exact_fit | `1` | 146 |
| `vslideup_vx` | `m2` | `SingleIssue` | exact_fit | `False` | 146 |
| `vslideup_vx` | `m4` | `Latency` | non_identifiable | `0, 1, 2, 3, 4` | 178 |
| `vslideup_vx` | `m4` | `ReleaseAtCycles` | exact_fit | `18` | 178 |
| `vslideup_vx` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 178 |
| `vslideup_vx` | `m4` | `NumMicroOps` | exact_fit | `1` | 178 |
| `vslideup_vx` | `m4` | `SingleIssue` | exact_fit | `False` | 178 |
| `vsll_vv` | `m1` | `Latency` | exact_fit | `4` | 166 |
| `vsll_vv` | `m1` | `ReleaseAtCycles` | exact_fit | `1` | 166 |
| `vsll_vv` | `m1` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vsll_vv` | `m1` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vsll_vv` | `m1` | `SingleIssue` | exact_fit | `False` | 166 |
| `vsll_vv` | `m2` | `Latency` | exact_fit | `4` | 166 |
| `vsll_vv` | `m2` | `ReleaseAtCycles` | exact_fit | `2` | 166 |
| `vsll_vv` | `m2` | `ProcResource` | non_identifiable | `YuShuXinVPipe0, YuShuXinVPipe1` | 9 |
| `vsll_vv` | `m2` | `NumMicroOps` | exact_fit | `1` | 166 |
| `vsll_vv` | `m2` | `SingleIssue` | exact_fit | `False` | 166 |
| `vsll_vv` | `m4` | `Latency` | exact_fit | `4` | 198 |
| `vsll_vv` | `m4` | `ReleaseAtCycles` | exact_fit | `4` | 198 |
| `vsll_vv` | `m4` | `ProcResource` | non_identifiable | `YuShuXinAnyVPipe, YuShuXinVPipe0, YuShuXinVPipe1` | 198 |
| `vsll_vv` | `m4` | `NumMicroOps` | exact_fit | `1` | 198 |
| `vsll_vv` | `m4` | `SingleIssue` | exact_fit | `False` | 198 |

## Formula Fits

| Instruction | Field | Status | Formula | Residual |
| --- | --- | --- | --- | ---: |
| `vadd_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vadd_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vcpop_m` | `Latency` | insufficient_evidence | `n/a` | n/a |
| `vcpop_m` | `ReleaseAtCycles` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vdivu_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vdivu_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `viota_m` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `viota_m` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vmseq_vv` | `Latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vmseq_vv` | `ReleaseAtCycles` | exact_fit | `4 + 1 * LMUL` | 0 |
| `vmul_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vmul_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vredsum_vs` | `Latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vredsum_vs` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
| `vrgather_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vrgather_vv` | `ReleaseAtCycles` | approximate_fit | `0 + 5 * LMUL` | 7 |
| `vslideup_vx` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vslideup_vx` | `ReleaseAtCycles` | approximate_fit | `1 + 4 * LMUL` | 3 |
| `vsll_vv` | `Latency` | exact_fit | `4 + 0 * LMUL` | 0 |
| `vsll_vv` | `ReleaseAtCycles` | exact_fit | `0 + 1 * LMUL` | 0 |
