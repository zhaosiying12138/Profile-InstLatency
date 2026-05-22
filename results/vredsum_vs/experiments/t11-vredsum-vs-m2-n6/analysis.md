# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vredsum_vs/experiments/t11-vredsum-vs-m2-n6/trace.json`
- Experiment ID: `t11-vredsum-vs-m2-n6`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `synthetic_calibration`
- Instruction: `vredsum_vs`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 72 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `12` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `72` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 72 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t11-vredsum-vs-m2-n6` at `results/vredsum_vs/experiments/t11-vredsum-vs-m2-n6/trace.json`.
