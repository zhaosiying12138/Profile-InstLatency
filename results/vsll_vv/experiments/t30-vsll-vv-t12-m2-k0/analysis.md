# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vsll_vv/experiments/t30-vsll-vv-t12-m2-k0/trace.json`
- Experiment ID: `t30-vsll-vv-t12-m2-k0`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vsll_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 5 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `5` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `5` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 5 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t30-vsll-vv-t12-m2-k0` at `results/vsll_vv/experiments/t30-vsll-vv-t12-m2-k0/trace.json`.
