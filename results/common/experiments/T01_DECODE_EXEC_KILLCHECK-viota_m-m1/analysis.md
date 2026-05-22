# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/T01_DECODE_EXEC_KILLCHECK-viota_m-m1/trace.json`
- Experiment ID: `T01_DECODE_EXEC_KILLCHECK-viota_m-m1`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `dry_run`
- Instruction: `viota_m`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 6 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `6` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `6` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 6 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `T01_DECODE_EXEC_KILLCHECK-viota_m-m1` at `results/common/experiments/T01_DECODE_EXEC_KILLCHECK-viota_m-m1/trace.json`.
