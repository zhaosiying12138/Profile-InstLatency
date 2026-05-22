# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vdivu_vv/experiments/t12-vdivu-vv-m2-k36-vadd-vv/trace.json`
- Experiment ID: `t12-vdivu-vv-m2-k36-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vdivu_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 60 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `24` |
| `release_cycles` | `8` |
| `measured_delta_cycles` | `60` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 60 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
