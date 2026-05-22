# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vslideup_vx/experiments/t12-vslideup-vx-m4-k0-vadd-vv/trace.json`
- Experiment ID: `t12-vslideup-vx-m4-k0-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vslideup_vx`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 7 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `7` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `7` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 7 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t12-vslideup-vx-m4-k0-vadd-vv` at `results/vslideup_vx/experiments/t12-vslideup-vx-m4-k0-vadd-vv/trace.json`.
