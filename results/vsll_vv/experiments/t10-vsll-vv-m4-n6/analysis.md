# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vsll_vv/experiments/t10-vsll-vv-m4-n6/trace.json`
- Experiment ID: `t10-vsll-vv-m4-n6`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `synthetic_calibration`
- Instruction: `vsll_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 30 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `7` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `30` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 30 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t10-vsll-vv-m4-n6` at `results/vsll_vv/experiments/t10-vsll-vv-m4-n6/trace.json`.
