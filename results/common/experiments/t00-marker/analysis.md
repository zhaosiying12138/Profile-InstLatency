# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/t00-marker/trace.json`
- Experiment ID: `t00-marker`
- Template ID: `T00_BASELINE_MARKER`
- Mode: `synthetic_calibration`
- Instruction: `unknown`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 0 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `None` |
| `latency_cycles` | `1` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `0` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `t0` | `t1` | 0 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
