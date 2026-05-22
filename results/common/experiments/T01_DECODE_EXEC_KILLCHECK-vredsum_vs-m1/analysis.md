# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/T01_DECODE_EXEC_KILLCHECK-vredsum_vs-m1/trace.json`
- Experiment ID: `T01_DECODE_EXEC_KILLCHECK-vredsum_vs-m1`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `dry_run`
- Instruction: `vredsum_vs`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 9 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `9` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `9` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 9 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `T01_DECODE_EXEC_KILLCHECK-vredsum_vs-m1` at `results/common/experiments/T01_DECODE_EXEC_KILLCHECK-vredsum_vs-m1/trace.json`.
