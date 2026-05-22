# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vrgather_vv/experiments/t11-vrgather-vv-m1-n6/trace.json`
- Experiment ID: `t11-vrgather-vv-m1-n6`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `synthetic_calibration`
- Instruction: `vrgather_vv`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 42 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `7` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `42` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 42 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t11-vrgather-vv-m1-n6` at `results/vrgather_vv/experiments/t11-vrgather-vv-m1-n6/trace.json`.
