# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/t01-vslideup-vx-m1/trace.json`
- Experiment ID: `t01-vslideup-vx-m1`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `synthetic_calibration`
- Instruction: `vslideup_vx`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 4 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `4` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `4` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 4 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t01-vslideup-vx-m1` at `results/common/experiments/t01-vslideup-vx-m1/trace.json`.
