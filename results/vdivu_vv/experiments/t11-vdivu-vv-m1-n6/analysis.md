# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vdivu_vv/experiments/t11-vdivu-vv-m1-n6/trace.json`
- Experiment ID: `t11-vdivu-vv-m1-n6`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `synthetic_calibration`
- Instruction: `vdivu_vv`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 108 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `18` |
| `release_cycles` | `6` |
| `measured_delta_cycles` | `108` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 108 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t11-vdivu-vv-m1-n6` at `results/vdivu_vv/experiments/t11-vdivu-vv-m1-n6/trace.json`.
