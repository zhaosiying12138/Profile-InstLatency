# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vcpop_m/experiments/t21-vcpop-m-m4-n4/trace.json`
- Experiment ID: `t21-vcpop-m-m4-n4`
- Template ID: `T21_PAIR_WITH_SCALAR`
- Mode: `synthetic_calibration`
- Instruction: `vcpop_m`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 4 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `7` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `4` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 4 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t21-vcpop-m-m4-n4` at `results/vcpop_m/experiments/t21-vcpop-m-m4-n4/trace.json`.
