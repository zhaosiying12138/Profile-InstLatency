# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vslideup_vx/experiments/t30-vslideup-vx-t12-m1-k0/trace.json`
- Experiment ID: `t30-vslideup-vx-t12-m1-k0`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vslideup_vx`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 4 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `4` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `4` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 4 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t30-vslideup-vx-t12-m1-k0` at `results/vslideup_vx/experiments/t30-vslideup-vx-t12-m1-k0/trace.json`.
