# Experiment Quality Report

Mode: real_platform_profile
Gate status: PASS
Confidence: approved_real_platform
Human approval status: approved

This report is generated from trace inventory. Synthetic calibration traces remain separate from real-platform observations and do not count toward the real gate.

## Approval Blockers

- None; all real-platform gate checks passed.

## Trace Inventory

Result root: `results`
Trace files analyzed: 10851
Synthetic traces: 3191
Real-platform traces: 7660
Real gem5 traces: 7660
Unknown/conflicting traces: 0 unknown, 0 conflicting

Classification uses JSON `mode` and `backend`; result paths are not used.

## Coverage

Required templates are inferred from the non-baseline synthetic latency/resource inventory: `T10_INDEPENDENT_STREAM_THROUGHPUT`, `T11_SELF_RAW_CHAIN`, `T12_CONSUMER_RAW_GAP`, `T20_PAIRWISE_PIPE_CLASSIFICATION`, `T21_PAIR_WITH_SCALAR`, `T30_LMUL_SCALING`, `T40_COMMON_VLSU_LOAD_HIT`.
Real gem5 templates covered: `T00_BASELINE_MARKER`, `T01_DECODE_EXEC_KILLCHECK`, `T10_INDEPENDENT_STREAM_THROUGHPUT`, `T11_SELF_RAW_CHAIN`, `T12_CONSUMER_RAW_GAP`, `T20_PAIRWISE_PIPE_CLASSIFICATION`, `T21_PAIR_WITH_SCALAR`, `T30_LMUL_SCALING`, `T40_COMMON_VLSU_LOAD_HIT`.

| Coverage field | Count |
| --- | ---: |
| Required template/instruction/LMUL groups | 178 |
| Covered required real gem5 groups | 178 |
| Missing required real gem5 groups | 0 |

## Repeatability

Repeat groups found: 3815
Stable repeat groups: 3815
Unstable repeat groups: 0

The complete repeatability table is split to keep documentation files reviewable:

- [Repeatability rows 1-1908](experiment_quality_repeatability_part1.md)
- [Repeatability rows 1909-3815](experiment_quality_repeatability_part2.md)

## Confidence

Computed confidence level: `approved_real_platform`.
No failed gate checks.

## LLVM Field Status

Field-status artifact: `results/common/real_platform_field_status.json`
Artifact present: true
Artifact sha256: `079cb94d27e98bdcf9df0ae0595a6e12b101e4c8c5a3d46f7d627dd4c81c1432`
Field-status summary: `blocked`
Required LLVM-facing fields: `Latency`, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, `SingleIssue`
Status records: 150

| Field status | Count |
| --- | ---: |
| `inferred` | 141 |
| `non_identifiable` | 9 |

Unresolved field-status risks:

| Risk ID | Instruction | LMUL | Field | Status | Reason |
| --- | --- | --- | --- | --- | --- |
| `llvm_field_status:vcpop_m:m1:Latency:non_identifiable` | `vcpop_m` | `m1` | `Latency` | `non_identifiable` | T12 consumer-gap observations provide only a conservative upper bound for Latency (Latency <= 1); the shared simulator filters candidate tuples with that bound but does not render a fake exact value. |
| `llvm_field_status:vcpop_m:m2:Latency:non_identifiable` | `vcpop_m` | `m2` | `Latency` | `non_identifiable` | T12 consumer-gap observations provide only a conservative upper bound for Latency (Latency <= 2); the shared simulator filters candidate tuples with that bound but does not render a fake exact value. |
| `llvm_field_status:vcpop_m:m4:Latency:non_identifiable` | `vcpop_m` | `m4` | `Latency` | `non_identifiable` | T12 consumer-gap observations provide only a conservative upper bound for Latency (Latency <= 4); the shared simulator filters candidate tuples with that bound but does not render a fake exact value. |
| `llvm_field_status:vcpop_m:m4:ReleaseAtCycles:non_identifiable` | `vcpop_m` | `m4` | `ReleaseAtCycles` | `non_identifiable` | The real-platform stream observations are not affine under the LLVM-facing startup+(N-1)*ReleaseAtCycles model. The profiler records the evidence but does not claim this field without a follow-up model for the extra platform effect. |
| `llvm_field_status:vcpop_m:m4:ProcResource:non_identifiable` | `vcpop_m` | `m4` | `ProcResource` | `non_identifiable` | The real-platform stream observations are not affine under the LLVM-facing startup+(N-1)*ReleaseAtCycles model. The profiler records the evidence but does not claim this field without a follow-up model for the extra platform effect. |
| `llvm_field_status:vcpop_m:m4:NumMicroOps:non_identifiable` | `vcpop_m` | `m4` | `NumMicroOps` | `non_identifiable` | The real-platform stream observations are not affine under the LLVM-facing startup+(N-1)*ReleaseAtCycles model. The profiler records the evidence but does not claim this field without a follow-up model for the extra platform effect. |
| `llvm_field_status:vcpop_m:m4:SingleIssue:non_identifiable` | `vcpop_m` | `m4` | `SingleIssue` | `non_identifiable` | The real-platform stream observations are not affine under the LLVM-facing startup+(N-1)*ReleaseAtCycles model. The profiler records the evidence but does not claim this field without a follow-up model for the extra platform effect. |
| `llvm_field_status:vrgather_vv:m4:Latency:non_identifiable` | `vrgather_vv` | `m4` | `Latency` | `non_identifiable` | T12 consumer-gap observations provide only a conservative upper bound for Latency (Latency <= 4); the shared simulator filters candidate tuples with that bound but does not render a fake exact value. |
| `llvm_field_status:vslideup_vx:m4:Latency:non_identifiable` | `vslideup_vx` | `m4` | `Latency` | `non_identifiable` | T12 consumer-gap observations provide only a conservative upper bound for Latency (Latency <= 4); the shared simulator filters candidate tuples with that bound but does not render a fake exact value. |

## Marker Contract

Contract status: `PASS`
Contract: `zero_cost_label_pc_wrapper`
TIMESTAMP_MARK is implemented as a zero-cost label-PC wrapper. Marker labels emit no instructions; the marker cycle is recovered from the first Exec-log instruction at the marker PC.
Checked real gem5 T00 traces: 2
No marker-contract failures.

## Conflicts

No unresolved conflicts detected in real-platform repeat or mode/backend classification data.

## Assumptions

- Real-platform approval is based on gem5 traces classified by trace JSON mode/backend fields, not by result path.
- Synthetic calibration traces remain reference-only for mismatch reporting and are not counted as real-platform coverage.
- Required real templates are inferred from non-baseline synthetic template inventory because that inventory defines the current latency/resource suite.
- Repeated measurements mean at least two real gem5 traces for the same template/instruction/LMUL/body signature with identical corrected primary deltas.
- Timestamp markers use the documented label-PC wrapper: marker labels emit no instructions, adjacent marker labels may share one PC, and the checked-in real T00 baseline must show zero corrected marker delta.

## Human Approval

Approval artifact: `results/common/human_approval.json`
Approval accepted by gate: true
The real gate cannot pass without clean field-status evidence or explicit per-risk acceptance, plus an approved human approval artifact tied to the real-platform inventory and field-status hashes.

## Machine-Readable Sidecar

See `results/common/real_platform_inventory.json` for the complete computed inventory, including exact missing group lists.
