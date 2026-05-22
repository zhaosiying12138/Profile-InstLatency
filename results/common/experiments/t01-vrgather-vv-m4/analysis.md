# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/t01-vrgather-vv-m4/trace.json`
- Experiment ID: `t01-vrgather-vv-m4`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `synthetic_calibration`
- Instruction: `vrgather_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 13 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `13` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `13` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 13 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t01-vrgather-vv-m4` at `results/common/experiments/t01-vrgather-vv-m4/trace.json`.
