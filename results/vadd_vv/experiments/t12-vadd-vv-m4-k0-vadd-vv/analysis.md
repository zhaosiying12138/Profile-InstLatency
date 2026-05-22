# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vadd_vv/experiments/t12-vadd-vv-m4-k0-vadd-vv/trace.json`
- Experiment ID: `t12-vadd-vv-m4-k0-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vadd_vv`
- LMUL: `m4`
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

For synthetic calibration, configured latency, release, and pipe come from `t12-vadd-vv-m4-k0-vadd-vv` at `results/vadd_vv/experiments/t12-vadd-vv-m4-k0-vadd-vv/trace.json`.
