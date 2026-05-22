# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vcpop_m/experiments/t30-vcpop-m-t12-m1-k9/trace.json`
- Experiment ID: `t30-vcpop-m-t12-m1-k9`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vcpop_m`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 13 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `4` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `13` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 13 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
