# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vsll_vv/experiments/t11-vsll-vv-m4-n6/trace.json`
- Experiment ID: `t11-vsll-vv-m4-n6`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `synthetic_calibration`
- Instruction: `vsll_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 42 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `7` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `42` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 42 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t11-vsll-vv-m4-n6` at `results/vsll_vv/experiments/t11-vsll-vv-m4-n6/trace.json`.
