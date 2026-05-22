# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/viota_m/experiments/t11-viota-m-m2-n4/trace.json`
- Experiment ID: `t11-viota-m-m2-n4`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `synthetic_calibration`
- Instruction: `viota_m`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 32 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `8` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `32` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 32 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
