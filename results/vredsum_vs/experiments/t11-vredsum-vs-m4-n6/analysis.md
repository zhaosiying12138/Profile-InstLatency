# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vredsum_vs/experiments/t11-vredsum-vs-m4-n6/trace.json`
- Experiment ID: `t11-vredsum-vs-m4-n6`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `synthetic_calibration`
- Instruction: `vredsum_vs`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 108 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `18` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `108` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 108 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t11-vredsum-vs-m4-n6` at `results/vredsum_vs/experiments/t11-vredsum-vs-m4-n6/trace.json`.
