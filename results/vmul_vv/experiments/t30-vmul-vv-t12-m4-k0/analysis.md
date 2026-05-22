# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vmul_vv/experiments/t30-vmul-vv-t12-m4-k0/trace.json`
- Experiment ID: `t30-vmul-vv-t12-m4-k0`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vmul_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 9 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `9` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `9` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 9 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t30-vmul-vv-t12-m4-k0` at `results/vmul_vv/experiments/t30-vmul-vv-t12-m4-k0/trace.json`.
