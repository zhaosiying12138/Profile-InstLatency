# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vrgather_vv/experiments/t30-vrgather-vv-t12-m2-k0/trace.json`
- Experiment ID: `t30-vrgather-vv-t12-m2-k0`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vrgather_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 9 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `9` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `9` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 9 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t30-vrgather-vv-t12-m2-k0` at `results/vrgather_vv/experiments/t30-vrgather-vv-t12-m2-k0/trace.json`.
