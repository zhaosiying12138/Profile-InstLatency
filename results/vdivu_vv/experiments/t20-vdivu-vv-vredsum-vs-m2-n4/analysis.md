# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vdivu_vv/experiments/t20-vdivu-vv-vredsum-vs-m2-n4/trace.json`
- Experiment ID: `t20-vdivu-vv-vredsum-vs-m2-n4`
- Template ID: `T20_PAIRWISE_PIPE_CLASSIFICATION`
- Mode: `synthetic_calibration`
- Instruction: `vdivu_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 32 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `24` |
| `release_cycles` | `8` |
| `measured_delta_cycles` | `32` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 32 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t20-vdivu-vv-vredsum-vs-m2-n4` at `results/vdivu_vv/experiments/t20-vdivu-vv-vredsum-vs-m2-n4/trace.json`.
