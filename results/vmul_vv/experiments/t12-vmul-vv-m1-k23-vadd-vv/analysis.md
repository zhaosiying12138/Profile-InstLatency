# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vmul_vv/experiments/t12-vmul-vv-m1-k23-vadd-vv/trace.json`
- Experiment ID: `t12-vmul-vv-m1-k23-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vmul_vv`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 29 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `6` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `29` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 29 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
