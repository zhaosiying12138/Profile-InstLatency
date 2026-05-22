# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vmul_vv/experiments/t20-vmul-vv-vdivu-vv-m4-n3/trace.json`
- Experiment ID: `t20-vmul-vv-vdivu-vv-m4-n3`
- Template ID: `T20_PAIRWISE_PIPE_CLASSIFICATION`
- Mode: `synthetic_calibration`
- Instruction: `vmul_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 15 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `9` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `15` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 15 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t20-vmul-vv-vdivu-vv-m4-n3` at `results/vmul_vv/experiments/t20-vmul-vv-vdivu-vv-m4-n3/trace.json`.
