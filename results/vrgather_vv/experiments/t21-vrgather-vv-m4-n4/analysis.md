# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vrgather_vv/experiments/t21-vrgather-vv-m4-n4/trace.json`
- Experiment ID: `t21-vrgather-vv-m4-n4`
- Template ID: `T21_PAIR_WITH_SCALAR`
- Mode: `synthetic_calibration`
- Instruction: `vrgather_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 20 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `13` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `20` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 20 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t21-vrgather-vv-m4-n4` at `results/vrgather_vv/experiments/t21-vrgather-vv-m4-n4/trace.json`.
