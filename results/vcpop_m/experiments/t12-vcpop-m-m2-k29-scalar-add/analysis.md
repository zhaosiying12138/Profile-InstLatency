# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vcpop_m/experiments/t12-vcpop-m-m2-k29-scalar-add/trace.json`
- Experiment ID: `t12-vcpop-m-m2-k29-scalar-add`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vcpop_m`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 34 cycles

## Synthetic Reference Metadata

Synthetic values are reference-only and are not used as LLVM-facing claims.

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `pipe0` |
| `latency_cycles` | `5` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `34` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 34 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
