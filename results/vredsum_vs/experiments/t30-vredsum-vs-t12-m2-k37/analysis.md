# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vredsum_vs/experiments/t30-vredsum-vs-t12-m2-k37/trace.json`
- Experiment ID: `t30-vredsum-vs-t12-m2-k37`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vredsum_vs`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 49 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `12` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `49` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 49 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
