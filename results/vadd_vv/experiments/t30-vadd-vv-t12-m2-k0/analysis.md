# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vadd_vv/experiments/t30-vadd-vv-t12-m2-k0/trace.json`
- Experiment ID: `t30-vadd-vv-t12-m2-k0`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vadd_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 2 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `2` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `2` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 2 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t30-vadd-vv-t12-m2-k0` at `results/vadd_vv/experiments/t30-vadd-vv-t12-m2-k0/trace.json`.
