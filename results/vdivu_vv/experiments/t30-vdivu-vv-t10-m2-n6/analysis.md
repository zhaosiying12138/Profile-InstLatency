# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vdivu_vv/experiments/t30-vdivu-vv-t10-m2-n6/trace.json`
- Experiment ID: `t30-vdivu-vv-t10-m2-n6`
- Template ID: `T30_LMUL_SCALING`
- Mode: `synthetic_calibration`
- Instruction: `vdivu_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 48 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `24` |
| `release_cycles` | `8` |
| `measured_delta_cycles` | `48` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 48 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
