# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vrgather_vv/experiments/t12-vrgather-vv-m4-k0-vadd-vv/trace.json`
- Experiment ID: `t12-vrgather-vv-m4-k0-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vrgather_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 13 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `13` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `13` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 13 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t12-vrgather-vv-m4-k0-vadd-vv` at `results/vrgather_vv/experiments/t12-vrgather-vv-m4-k0-vadd-vv/trace.json`.
