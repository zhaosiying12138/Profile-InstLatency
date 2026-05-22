# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vmul_vv/experiments/t11-vmul-vv-m2-n2/trace.json`
- Experiment ID: `t11-vmul-vv-m2-n2`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `synthetic_calibration`
- Instruction: `vmul_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 14 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `7` |
| `release_cycles` | `3` |
| `measured_delta_cycles` | `14` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 14 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
