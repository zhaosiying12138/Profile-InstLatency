# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vredsum_vs/experiments/t30-vredsum-vs-t12-m4-k0/trace.json`
- Experiment ID: `t30-vredsum-vs-t12-m4-k0`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vredsum_vs`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 18 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `18` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `18` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 18 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t30-vredsum-vs-t12-m4-k0` at `results/vredsum_vs/experiments/t30-vredsum-vs-t12-m4-k0/trace.json`.
