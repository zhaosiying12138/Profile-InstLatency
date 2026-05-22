# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/viota_m/experiments/t20-viota-m-vslideup-vx-m1-n4/trace.json`
- Experiment ID: `t20-viota-m-vslideup-vx-m1-n4`
- Template ID: `T20_PAIRWISE_PIPE_CLASSIFICATION`
- Mode: `synthetic_calibration`
- Instruction: `viota_m`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 12 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `6` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `12` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 12 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
