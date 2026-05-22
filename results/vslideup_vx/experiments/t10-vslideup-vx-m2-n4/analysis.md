# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vslideup_vx/experiments/t10-vslideup-vx-m2-n4/trace.json`
- Experiment ID: `t10-vslideup-vx-m2-n4`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `synthetic_calibration`
- Instruction: `vslideup_vx`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 4 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `5` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `4` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 4 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
