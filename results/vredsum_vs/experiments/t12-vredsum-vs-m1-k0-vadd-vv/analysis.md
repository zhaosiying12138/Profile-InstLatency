# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vredsum_vs/experiments/t12-vredsum-vs-m1-k0-vadd-vv/trace.json`
- Experiment ID: `t12-vredsum-vs-m1-k0-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vredsum_vs`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 9 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `9` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `9` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 9 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t12-vredsum-vs-m1-k0-vadd-vv` at `results/vredsum_vs/experiments/t12-vredsum-vs-m1-k0-vadd-vv/trace.json`.
