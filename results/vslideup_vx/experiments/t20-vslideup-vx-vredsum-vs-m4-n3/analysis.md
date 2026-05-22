# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vslideup_vx/experiments/t20-vslideup-vx-vredsum-vs-m4-n3/trace.json`
- Experiment ID: `t20-vslideup-vx-vredsum-vs-m4-n3`
- Template ID: `T20_PAIRWISE_PIPE_CLASSIFICATION`
- Mode: `synthetic_calibration`
- Instruction: `vslideup_vx`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 3 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `7` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `3` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 3 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t20-vslideup-vx-vredsum-vs-m4-n3` at `results/vslideup_vx/experiments/t20-vslideup-vx-vredsum-vs-m4-n3/trace.json`.
