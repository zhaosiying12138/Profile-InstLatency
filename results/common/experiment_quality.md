# Experiment Quality Report

Mode: real_platform_profile
Gate status: NOT_READY
Confidence: awaiting_human_approval
Human approval status: absent

This report is generated from trace inventory. Synthetic calibration traces remain separate from real-platform observations and do not count toward the real gate.

## Approval Blockers

- Explicit human approval artifact: absent or not approved.

## Trace Inventory

Result root: `results`
Trace files analyzed: 10411
Synthetic traces: 3191
Real-platform traces: 7220
Real gem5 traces: 7220
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

Repeat groups found: 3595
Stable repeat groups: 3595
Unstable repeat groups: 0

The full repeatability table is split into linked companion files to keep each generated document below the repository line limit.

- [Repeatability rows 1-1798](experiment_quality_repeatability_part1.md)
- [Repeatability rows 1799-3595](experiment_quality_repeatability_part2.md)

## Confidence

Computed confidence level: `awaiting_human_approval`.
Failed gate checks:
- `explicit_human_approval`

## LLVM Field Status

Field-status artifact: `results/common/real_platform_field_status.json`
Artifact present: true
Artifact sha256: `16be9c8910a119669b1653d961a1c8707b1bcf4d6e04a5e7d4502e0af0685d8f`
Field-status summary: `ready`
Required LLVM-facing fields: `Latency`, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, `SingleIssue`
Status records: 150

| Field status | Count |
| --- | ---: |
| `inferred` | 102 |
| `non_identifiable` | 48 |
No unresolved field-status risks.

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

Approval artifact: absent
The real gate cannot pass without clean field-status evidence or explicit per-risk acceptance, plus an approved human approval artifact tied to the real-platform inventory and field-status hashes.

## Machine-Readable Sidecar

See `results/common/real_platform_inventory.json` for the complete computed inventory, including exact missing group lists.
