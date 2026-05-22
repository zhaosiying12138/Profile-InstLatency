# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vredsum_vs/experiments/t30-vredsum-vs-t11-m4-n6/trace.json`
- Experiment ID: `t30-vredsum-vs-t11-m4-n6`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vredsum_vs`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 108 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `18` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `108` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 108 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
