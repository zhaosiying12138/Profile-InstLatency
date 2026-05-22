# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/viota_m/experiments/t21-viota-m-m1-n4/trace.json`
- Experiment ID: `t21-viota-m-m1-n4`
- Template ID: `T21_PAIR_WITH_SCALAR`
- Mode: `synthetic_calibration`
- Instruction: `viota_m`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 8 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `6` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `8` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 8 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t21-viota-m-m1-n4` at `results/viota_m/experiments/t21-viota-m-m1-n4/trace.json`.
