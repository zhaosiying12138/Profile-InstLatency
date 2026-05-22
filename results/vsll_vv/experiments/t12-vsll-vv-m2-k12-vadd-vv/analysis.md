# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vsll_vv/experiments/t12-vsll-vv-m2-k12-vadd-vv/trace.json`
- Experiment ID: `t12-vsll-vv-m2-k12-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vsll_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 17 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `5` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `17` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 17 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
