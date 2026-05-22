# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vadd_vv/experiments/t20-vadd-vv-vrgather-vv-m1-n4/trace.json`
- Experiment ID: `t20-vadd-vv-vrgather-vv-m1-n4`
- Template ID: `T20_PAIRWISE_PIPE_CLASSIFICATION`
- Mode: `synthetic_calibration`
- Instruction: `vadd_vv`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 4 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `2` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `4` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 4 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t20-vadd-vv-vrgather-vv-m1-n4` at `results/vadd_vv/experiments/t20-vadd-vv-vrgather-vv-m1-n4/trace.json`.
