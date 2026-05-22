# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vredsum_vs/experiments/t12-vredsum-vs-m4-k36-vadd-vv/trace.json`
- Experiment ID: `t12-vredsum-vs-m4-k36-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vredsum_vs`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 54 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `18` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `54` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 54 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
