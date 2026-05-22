# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/T01_DECODE_EXEC_KILLCHECK-vslideup_vx-m2/trace.json`
- Experiment ID: `T01_DECODE_EXEC_KILLCHECK-vslideup_vx-m2`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `dry_run`
- Instruction: `vslideup_vx`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 5 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `5` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `5` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 5 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `T01_DECODE_EXEC_KILLCHECK-vslideup_vx-m2` at `results/common/experiments/T01_DECODE_EXEC_KILLCHECK-vslideup_vx-m2/trace.json`.
