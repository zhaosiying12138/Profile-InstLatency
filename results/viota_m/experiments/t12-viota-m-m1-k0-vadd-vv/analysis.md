# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/viota_m/experiments/t12-viota-m-m1-k0-vadd-vv/trace.json`
- Experiment ID: `t12-viota-m-m1-k0-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `viota_m`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 6 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `6` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `6` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 6 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t12-viota-m-m1-k0-vadd-vv` at `results/viota_m/experiments/t12-viota-m-m1-k0-vadd-vv/trace.json`.
