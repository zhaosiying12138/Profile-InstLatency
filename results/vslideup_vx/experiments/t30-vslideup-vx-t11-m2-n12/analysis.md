# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vslideup_vx/experiments/t30-vslideup-vx-t11-m2-n12/trace.json`
- Experiment ID: `t30-vslideup-vx-t11-m2-n12`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vslideup_vx`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 60 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `5` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `60` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 60 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
