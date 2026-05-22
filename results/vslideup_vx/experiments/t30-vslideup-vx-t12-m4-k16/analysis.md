# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vslideup_vx/experiments/t30-vslideup-vx-t12-m4-k16/trace.json`
- Experiment ID: `t30-vslideup-vx-t12-m4-k16`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vslideup_vx`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 23 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `7` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `23` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 23 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
