# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vdivu_vv/experiments/t20-vdivu-vv-viota-m-m4-n3/trace.json`
- Experiment ID: `t20-vdivu-vv-viota-m-m4-n3`
- Template ID: `T20_PAIRWISE_PIPE_CLASSIFICATION`
- Mode: `synthetic_calibration`
- Instruction: `vdivu_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 36 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe1` |
| `latency_cycles` | `36` |
| `release_cycles` | `12` |
| `measured_delta_cycles` | `36` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 36 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
