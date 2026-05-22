# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/viota_m/experiments/t11-viota-m-m4-n2/trace.json`
- Experiment ID: `t11-viota-m-m4-n2`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `synthetic_calibration`
- Instruction: `viota_m`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 24 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `12` |
| `release_cycles` | `5` |
| `measured_delta_cycles` | `24` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 24 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
