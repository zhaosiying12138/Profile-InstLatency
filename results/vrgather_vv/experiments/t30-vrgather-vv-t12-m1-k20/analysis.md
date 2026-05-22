# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vrgather_vv/experiments/t30-vrgather-vv-t12-m1-k20/trace.json`
- Experiment ID: `t30-vrgather-vv-t12-m1-k20`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vrgather_vv`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 27 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `7` |
| `release_cycles` | `2` |
| `measured_delta_cycles` | `27` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 27 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
