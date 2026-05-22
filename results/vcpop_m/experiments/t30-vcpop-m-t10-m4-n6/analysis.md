# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vcpop_m/experiments/t30-vcpop-m-t10-m4-n6/trace.json`
- Experiment ID: `t30-vcpop-m-t10-m4-n6`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vcpop_m`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 6 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `7` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `6` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 6 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t30-vcpop-m-t10-m4-n6` at `results/vcpop_m/experiments/t30-vcpop-m-t10-m4-n6/trace.json`.
