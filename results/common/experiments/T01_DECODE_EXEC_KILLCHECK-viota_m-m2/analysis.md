# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/T01_DECODE_EXEC_KILLCHECK-viota_m-m2/trace.json`
- Experiment ID: `T01_DECODE_EXEC_KILLCHECK-viota_m-m2`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `dry_run`
- Instruction: `viota_m`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 8 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `8` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `8` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 8 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `T01_DECODE_EXEC_KILLCHECK-viota_m-m2` at `results/common/experiments/T01_DECODE_EXEC_KILLCHECK-viota_m-m2/trace.json`.
