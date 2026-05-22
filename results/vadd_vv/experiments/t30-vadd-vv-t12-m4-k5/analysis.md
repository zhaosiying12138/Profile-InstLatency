# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vadd_vv/experiments/t30-vadd-vv-t12-m4-k5/trace.json`
- Experiment ID: `t30-vadd-vv-t12-m4-k5`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vadd_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 7 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `2` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `7` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 7 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
