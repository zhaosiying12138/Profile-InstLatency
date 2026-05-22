# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vsll_vv/experiments/t21-vsll-vv-m4-n4/trace.json`
- Experiment ID: `t21-vsll-vv-m4-n4`
- Template ID: `T21_PAIR_WITH_SCALAR`
- Mode: `synthetic_calibration`
- Instruction: `vsll_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 20 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `7` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `20` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 20 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t21-vsll-vv-m4-n4` at `results/vsll_vv/experiments/t21-vsll-vv-m4-n4/trace.json`.
