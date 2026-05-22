# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vredsum_vs/experiments/t21-vredsum-vs-m1-n4/trace.json`
- Experiment ID: `t21-vredsum-vs-m1-n4`
- Template ID: `T21_PAIR_WITH_SCALAR`
- Mode: `synthetic_calibration`
- Instruction: `vredsum_vs`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 8 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `9` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `8` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 8 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t21-vredsum-vs-m1-n4` at `results/vredsum_vs/experiments/t21-vredsum-vs-m1-n4/trace.json`.
