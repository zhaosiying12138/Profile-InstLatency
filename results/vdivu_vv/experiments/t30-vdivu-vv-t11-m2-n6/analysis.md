# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vdivu_vv/experiments/t30-vdivu-vv-t11-m2-n6/trace.json`
- Experiment ID: `t30-vdivu-vv-t11-m2-n6`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vdivu_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 144 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `24` |
| `release_cycles` | `8` |
| `measured_delta_cycles` | `144` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 144 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t30-vdivu-vv-t11-m2-n6` at `results/vdivu_vv/experiments/t30-vdivu-vv-t11-m2-n6/trace.json`.
