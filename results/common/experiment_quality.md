# Experiment Quality Report

Mode: real_platform_profile
Gate status: NOT_READY
Confidence: insufficient_real_coverage
Human approval status: absent

This report is generated from trace inventory. Synthetic calibration traces remain separate from real-platform observations and do not count toward the real gate.

## Approval Blockers

- Missing real gem5 template coverage: `T10_INDEPENDENT_STREAM_THROUGHPUT`, `T11_SELF_RAW_CHAIN`, `T12_CONSUMER_RAW_GAP`, `T20_PAIRWISE_PIPE_CLASSIFICATION`, `T21_PAIR_WITH_SCALAR`, `T30_LMUL_SCALING`, `T40_COMMON_VLSU_LOAD_HIT`.
- Missing real gem5 template/instruction/LMUL groups: 178.
- Missing stable repeated real gem5 measurements: 178 groups.
- Explicit human approval artifact: absent or not approved.

## Trace Inventory

Result root: `results`
Trace files analyzed: 3221
Synthetic traces: 3191
Real-platform traces: 30
Real gem5 traces: 30
Unknown/conflicting traces: 0 unknown, 0 conflicting

Classification uses JSON `mode` and `backend`; result paths are not used.

## Coverage

Required templates are inferred from the non-baseline synthetic latency/resource inventory: `T10_INDEPENDENT_STREAM_THROUGHPUT`, `T11_SELF_RAW_CHAIN`, `T12_CONSUMER_RAW_GAP`, `T20_PAIRWISE_PIPE_CLASSIFICATION`, `T21_PAIR_WITH_SCALAR`, `T30_LMUL_SCALING`, `T40_COMMON_VLSU_LOAD_HIT`.
Real gem5 templates covered: `T01_DECODE_EXEC_KILLCHECK`.

| Coverage field | Count |
| --- | ---: |
| Required template/instruction/LMUL groups | 178 |
| Covered required real gem5 groups | 0 |
| Missing required real gem5 groups | 178 |

Missing required real gem5 groups by template:

| Template | Missing groups |
| --- | ---: |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | 30 |
| `T11_SELF_RAW_CHAIN` | 30 |
| `T12_CONSUMER_RAW_GAP` | 30 |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | 27 |
| `T21_PAIR_WITH_SCALAR` | 30 |
| `T30_LMUL_SCALING` | 30 |
| `T40_COMMON_VLSU_LOAD_HIT` | 1 |

Missing required real gem5 groups:

| Template | Instruction | LMUL |
| --- | --- | --- |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vadd_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vadd_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vadd_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vcpop_m` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vcpop_m` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vcpop_m` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vdivu_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vdivu_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vdivu_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `viota_m` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `viota_m` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `viota_m` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmseq_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmseq_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmseq_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmul_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmul_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmul_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vredsum_vs` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vredsum_vs` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vredsum_vs` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vrgather_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vrgather_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vrgather_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vslideup_vx` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vslideup_vx` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vslideup_vx` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vsll_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vsll_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vsll_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vadd_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vadd_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vadd_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vcpop_m` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vcpop_m` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vcpop_m` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vdivu_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vdivu_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vdivu_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `viota_m` | `m1` |
| `T11_SELF_RAW_CHAIN` | `viota_m` | `m2` |
| `T11_SELF_RAW_CHAIN` | `viota_m` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vmseq_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vmseq_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vmseq_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vmul_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vmul_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vmul_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vredsum_vs` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vredsum_vs` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vredsum_vs` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vrgather_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vrgather_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vrgather_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vslideup_vx` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vslideup_vx` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vslideup_vx` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vsll_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vsll_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vsll_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vadd_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vadd_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vadd_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vcpop_m` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vcpop_m` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vcpop_m` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vdivu_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vdivu_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vdivu_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `viota_m` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `viota_m` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `viota_m` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vmseq_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vmseq_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vmseq_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vmul_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vmul_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vmul_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vredsum_vs` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vredsum_vs` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vredsum_vs` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vrgather_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vrgather_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vrgather_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vslideup_vx` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vslideup_vx` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vslideup_vx` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vsll_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vsll_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vsll_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vadd_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vadd_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vadd_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vcpop_m` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vcpop_m` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vcpop_m` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vdivu_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vdivu_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vdivu_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `viota_m` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `viota_m` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `viota_m` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmseq_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmseq_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmseq_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmul_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmul_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmul_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vrgather_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vrgather_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vrgather_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vslideup_vx` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vslideup_vx` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vslideup_vx` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vsll_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vsll_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vsll_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vadd_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vadd_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vadd_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vcpop_m` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vcpop_m` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vcpop_m` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vdivu_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vdivu_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vdivu_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `viota_m` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `viota_m` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `viota_m` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vmseq_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vmseq_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vmseq_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vmul_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vmul_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vmul_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vredsum_vs` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vredsum_vs` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vredsum_vs` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vrgather_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vrgather_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vrgather_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vslideup_vx` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vslideup_vx` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vslideup_vx` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vsll_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vsll_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vsll_vv` | `m4` |
| `T30_LMUL_SCALING` | `vadd_vv` | `m1` |
| `T30_LMUL_SCALING` | `vadd_vv` | `m2` |
| `T30_LMUL_SCALING` | `vadd_vv` | `m4` |
| `T30_LMUL_SCALING` | `vcpop_m` | `m1` |
| `T30_LMUL_SCALING` | `vcpop_m` | `m2` |
| `T30_LMUL_SCALING` | `vcpop_m` | `m4` |
| `T30_LMUL_SCALING` | `vdivu_vv` | `m1` |
| `T30_LMUL_SCALING` | `vdivu_vv` | `m2` |
| `T30_LMUL_SCALING` | `vdivu_vv` | `m4` |
| `T30_LMUL_SCALING` | `viota_m` | `m1` |
| `T30_LMUL_SCALING` | `viota_m` | `m2` |
| `T30_LMUL_SCALING` | `viota_m` | `m4` |
| `T30_LMUL_SCALING` | `vmseq_vv` | `m1` |
| `T30_LMUL_SCALING` | `vmseq_vv` | `m2` |
| `T30_LMUL_SCALING` | `vmseq_vv` | `m4` |
| `T30_LMUL_SCALING` | `vmul_vv` | `m1` |
| `T30_LMUL_SCALING` | `vmul_vv` | `m2` |
| `T30_LMUL_SCALING` | `vmul_vv` | `m4` |
| `T30_LMUL_SCALING` | `vredsum_vs` | `m1` |
| `T30_LMUL_SCALING` | `vredsum_vs` | `m2` |
| `T30_LMUL_SCALING` | `vredsum_vs` | `m4` |
| `T30_LMUL_SCALING` | `vrgather_vv` | `m1` |
| `T30_LMUL_SCALING` | `vrgather_vv` | `m2` |
| `T30_LMUL_SCALING` | `vrgather_vv` | `m4` |
| `T30_LMUL_SCALING` | `vslideup_vx` | `m1` |
| `T30_LMUL_SCALING` | `vslideup_vx` | `m2` |
| `T30_LMUL_SCALING` | `vslideup_vx` | `m4` |
| `T30_LMUL_SCALING` | `vsll_vv` | `m1` |
| `T30_LMUL_SCALING` | `vsll_vv` | `m2` |
| `T30_LMUL_SCALING` | `vsll_vv` | `m4` |
| `T40_COMMON_VLSU_LOAD_HIT` | `unknown` | `m1` |

## Repeatability

Repeat groups found: 0
Stable repeat groups: 0
Unstable repeat groups: 0
No repeated real gem5 measurements are available.

Missing stable repeat groups by template:

| Template | Missing groups |
| --- | ---: |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | 30 |
| `T11_SELF_RAW_CHAIN` | 30 |
| `T12_CONSUMER_RAW_GAP` | 30 |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | 27 |
| `T21_PAIR_WITH_SCALAR` | 30 |
| `T30_LMUL_SCALING` | 30 |
| `T40_COMMON_VLSU_LOAD_HIT` | 1 |

Missing stable repeat groups:

| Template | Instruction | LMUL |
| --- | --- | --- |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vadd_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vadd_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vadd_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vcpop_m` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vcpop_m` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vcpop_m` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vdivu_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vdivu_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vdivu_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `viota_m` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `viota_m` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `viota_m` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmseq_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmseq_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmseq_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmul_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmul_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vmul_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vredsum_vs` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vredsum_vs` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vredsum_vs` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vrgather_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vrgather_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vrgather_vv` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vslideup_vx` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vslideup_vx` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vslideup_vx` | `m4` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vsll_vv` | `m1` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vsll_vv` | `m2` |
| `T10_INDEPENDENT_STREAM_THROUGHPUT` | `vsll_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vadd_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vadd_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vadd_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vcpop_m` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vcpop_m` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vcpop_m` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vdivu_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vdivu_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vdivu_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `viota_m` | `m1` |
| `T11_SELF_RAW_CHAIN` | `viota_m` | `m2` |
| `T11_SELF_RAW_CHAIN` | `viota_m` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vmseq_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vmseq_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vmseq_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vmul_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vmul_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vmul_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vredsum_vs` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vredsum_vs` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vredsum_vs` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vrgather_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vrgather_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vrgather_vv` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vslideup_vx` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vslideup_vx` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vslideup_vx` | `m4` |
| `T11_SELF_RAW_CHAIN` | `vsll_vv` | `m1` |
| `T11_SELF_RAW_CHAIN` | `vsll_vv` | `m2` |
| `T11_SELF_RAW_CHAIN` | `vsll_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vadd_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vadd_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vadd_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vcpop_m` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vcpop_m` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vcpop_m` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vdivu_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vdivu_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vdivu_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `viota_m` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `viota_m` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `viota_m` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vmseq_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vmseq_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vmseq_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vmul_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vmul_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vmul_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vredsum_vs` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vredsum_vs` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vredsum_vs` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vrgather_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vrgather_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vrgather_vv` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vslideup_vx` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vslideup_vx` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vslideup_vx` | `m4` |
| `T12_CONSUMER_RAW_GAP` | `vsll_vv` | `m1` |
| `T12_CONSUMER_RAW_GAP` | `vsll_vv` | `m2` |
| `T12_CONSUMER_RAW_GAP` | `vsll_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vadd_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vadd_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vadd_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vcpop_m` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vcpop_m` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vcpop_m` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vdivu_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vdivu_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vdivu_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `viota_m` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `viota_m` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `viota_m` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmseq_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmseq_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmseq_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmul_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmul_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vmul_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vrgather_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vrgather_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vrgather_vv` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vslideup_vx` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vslideup_vx` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vslideup_vx` | `m4` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vsll_vv` | `m1` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vsll_vv` | `m2` |
| `T20_PAIRWISE_PIPE_CLASSIFICATION` | `vsll_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vadd_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vadd_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vadd_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vcpop_m` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vcpop_m` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vcpop_m` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vdivu_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vdivu_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vdivu_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `viota_m` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `viota_m` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `viota_m` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vmseq_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vmseq_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vmseq_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vmul_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vmul_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vmul_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vredsum_vs` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vredsum_vs` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vredsum_vs` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vrgather_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vrgather_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vrgather_vv` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vslideup_vx` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vslideup_vx` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vslideup_vx` | `m4` |
| `T21_PAIR_WITH_SCALAR` | `vsll_vv` | `m1` |
| `T21_PAIR_WITH_SCALAR` | `vsll_vv` | `m2` |
| `T21_PAIR_WITH_SCALAR` | `vsll_vv` | `m4` |
| `T30_LMUL_SCALING` | `vadd_vv` | `m1` |
| `T30_LMUL_SCALING` | `vadd_vv` | `m2` |
| `T30_LMUL_SCALING` | `vadd_vv` | `m4` |
| `T30_LMUL_SCALING` | `vcpop_m` | `m1` |
| `T30_LMUL_SCALING` | `vcpop_m` | `m2` |
| `T30_LMUL_SCALING` | `vcpop_m` | `m4` |
| `T30_LMUL_SCALING` | `vdivu_vv` | `m1` |
| `T30_LMUL_SCALING` | `vdivu_vv` | `m2` |
| `T30_LMUL_SCALING` | `vdivu_vv` | `m4` |
| `T30_LMUL_SCALING` | `viota_m` | `m1` |
| `T30_LMUL_SCALING` | `viota_m` | `m2` |
| `T30_LMUL_SCALING` | `viota_m` | `m4` |
| `T30_LMUL_SCALING` | `vmseq_vv` | `m1` |
| `T30_LMUL_SCALING` | `vmseq_vv` | `m2` |
| `T30_LMUL_SCALING` | `vmseq_vv` | `m4` |
| `T30_LMUL_SCALING` | `vmul_vv` | `m1` |
| `T30_LMUL_SCALING` | `vmul_vv` | `m2` |
| `T30_LMUL_SCALING` | `vmul_vv` | `m4` |
| `T30_LMUL_SCALING` | `vredsum_vs` | `m1` |
| `T30_LMUL_SCALING` | `vredsum_vs` | `m2` |
| `T30_LMUL_SCALING` | `vredsum_vs` | `m4` |
| `T30_LMUL_SCALING` | `vrgather_vv` | `m1` |
| `T30_LMUL_SCALING` | `vrgather_vv` | `m2` |
| `T30_LMUL_SCALING` | `vrgather_vv` | `m4` |
| `T30_LMUL_SCALING` | `vslideup_vx` | `m1` |
| `T30_LMUL_SCALING` | `vslideup_vx` | `m2` |
| `T30_LMUL_SCALING` | `vslideup_vx` | `m4` |
| `T30_LMUL_SCALING` | `vsll_vv` | `m1` |
| `T30_LMUL_SCALING` | `vsll_vv` | `m2` |
| `T30_LMUL_SCALING` | `vsll_vv` | `m4` |
| `T40_COMMON_VLSU_LOAD_HIT` | `unknown` | `m1` |

## Confidence

Computed confidence level: `insufficient_real_coverage`.
Failed gate checks:
- `required_templates_covered_by_real_gem5`
- `required_template_instruction_lmul_covered_by_real_gem5`
- `stable_repeats_exist_for_required_groups`
- `explicit_human_approval`

## Conflicts

No unresolved conflicts detected in real-platform repeat or mode/backend classification data.

## Assumptions

- Real-platform approval is based on gem5 traces classified by trace JSON mode/backend fields, not by result path.
- Synthetic calibration traces remain reference-only for mismatch reporting and are not counted as real-platform coverage.
- Required real templates are inferred from non-baseline synthetic template inventory because that inventory defines the current latency/resource suite.
- Repeated measurements mean at least two real gem5 traces for the same template/instruction/LMUL/body signature with identical corrected primary deltas.
- Zero-cost timestamp-marker assumptions remain documented in per-trace metadata and are not revalidated by this analyzer.

## Human Approval

Approval artifact: absent
The real gate cannot pass without an explicit approved human approval artifact after this report is reviewed.

## Machine-Readable Sidecar

See `results/common/real_platform_inventory.json` for the complete computed inventory, including exact missing group lists.
