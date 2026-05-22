# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/t01-vredsum-vs-m2/trace.json`
- Experiment ID: `t01-vredsum-vs-m2`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `synthetic_calibration`
- Instruction: `vredsum_vs`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 12 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `12` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `12` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 12 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t01-vredsum-vs-m2` at `results/common/experiments/t01-vredsum-vs-m2/trace.json`.
