# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vsll_vv/experiments/t30-vsll-vv-t12-m2-k19/trace.json`
- Experiment ID: `t30-vsll-vv-t12-m2-k19`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vsll_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 24 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `5` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `24` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 24 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
